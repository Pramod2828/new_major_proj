import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from backend.models.registry import ModelRegistry
from backend.feature_engineering.log_parser import LogParser
from backend.explainability.shap_engine import ShapExplainabilityEngine
from backend.services.classification_policy import RiskClassificationPolicy
from backend.database.db import get_db, query_all, query_one, execute_write

class InferenceService:
    """Live log inference, three-level risk classification, and anomaly prediction service."""

    @classmethod
    def predict_logs(
        cls,
        raw_lines: List[str],
        compute_shap: bool = True,
        batch_id: Optional[str] = None,
        policy: Optional[RiskClassificationPolicy] = None,
        allow_unclassified: bool = False
    ) -> Dict[str, Any]:
        """Run anomaly detection and 3-level classification pipeline on raw log lines.
        
        Args:
            raw_lines: List of raw log strings
            compute_shap: Whether to compute SHAP contributions for predictions
            batch_id: Optional tracking identifier for the batch
            policy: Optional custom RiskClassificationPolicy instance
            allow_unclassified: Whether to allow logging unclassified events when no model is active
            
        Returns:
            Dictionary with batch statistics and per-record predictions.
        """
        parsed_records = LogParser.parse_batch(raw_lines)
        if not parsed_records:
            return {
                "success": False,
                "error": "No valid log records found in the provided input.",
                "total_processed": 0,
                "normal_count": 0,
                "medium_count": 0,
                "anomalous_count": 0,
                "unclassified_count": 0,
                "results": []
            }

        extracted_features_list = [LogParser.extract_features(r) for r in parsed_records]
        df_features = pd.DataFrame(extracted_features_list)
        now_ts = datetime.utcnow().isoformat()
        batch_uid = batch_id or f"batch_{uuid.uuid4().hex[:8]}"

        # Handle multiple active models
        active_models = ModelRegistry.get_active_models()

        # If still no active models, fallback to unclassified handling
        if not active_models:
            if not allow_unclassified:
                return {
                    "success": False,
                    "error": "No active model found. Please train and activate a model in the Model Registry before running inference.",
                    "total_processed": 0,
                    "normal_count": 0,
                    "medium_count": 0,
                    "anomalous_count": 0,
                    "unclassified_count": 0,
                    "results": []
                }
            # Unclassified processing as before (same as original block)
            cls_policy = policy or RiskClassificationPolicy()
            results = []
            with get_db() as conn:
                cursor = conn.cursor()
                for record, feat_dict in zip(parsed_records, extracted_features_list):
                    pred_id = f"pred_{uuid.uuid4().hex[:12]}"
                    category = "Unclassified"
                    raw_msg = record.get("message") or record.get("raw", "")
                    explanation_obj = cls_policy.build_explanation(
                        record=record,
                        features=feat_dict,
                        category=category,
                        probability=None,
                        confidence=None,
                        original_prediction=None,
                        shap_data=None,
                        model_meta=None
                    )
                    log_lvl = cls_policy._decode_log_level(record.get("severity"))

                    cursor.execute(
                        """INSERT INTO predictions (
                            id, batch_id, model_id, model_name, model_version,
                            raw_log, parsed_fields_json, features_json,
                            prediction, probability, is_anomaly, category,
                            risk_score, confidence, explanation_summary,
                            observed_facts_json, model_explanation_json, security_interpretation,
                            shap_values_json, timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            pred_id,
                            batch_uid,
                            "unclassified",
                            "None",
                            "N/A",
                            record.get("raw", ""),
                            json.dumps(record),
                            json.dumps(feat_dict),
                            -1,
                            None,
                            0,
                            category,
                            None,
                            None,
                            explanation_obj["summary"],
                            json.dumps(explanation_obj["observed_facts"]),
                            json.dumps(explanation_obj["model_explanation"]),
                            explanation_obj["security_interpretation"],
                            None,
                            record.get("timestamp") or now_ts
                        )
                    )

                    results.append({
                        "id": pred_id,
                        "raw_log": record.get("raw", ""),
                        "timestamp": record.get("timestamp") or now_ts,
                        "hostname": record.get("hostname") or "localhost",
                        "app_name": record.get("service") or "system",
                        "service": record.get("service") or "system",
                        "log_level": log_lvl,
                        "severity": record.get("severity"),
                        "message": raw_msg,
                        "classification": category,
                        "category": category,
                        "prediction": None,
                        "is_anomaly": False,
                        "probability": None,
                        "risk_score": None,
                        "confidence": None,
                        "explanation_summary": explanation_obj["summary"],
                        "observed_facts": explanation_obj["observed_facts"],
                        "model_explanation": explanation_obj["model_explanation"],
                        "security_interpretation": explanation_obj["security_interpretation"],
                        "shap": None
                    })
            # Return early for unclassified only path
            return {
                "success": True,
                "has_active_model": False,
                "batch_id": batch_uid,
                "model": None,
                "total_processed": len(results),
                "normal_count": 0,
                "medium_count": 0,
                "anomalous_count": 0,
                "unclassified_count": len(results),
                "normal_percentage": 0.0,
                "medium_percentage": 0.0,
                "anomalous_percentage": 0.0,
                "unclassified_percentage": 100.0,
                "results": results
            }

        # Process each active model separately and aggregate results
        all_results = []
        normal_count = medium_count = anomalous_count = unclassified_count = 0
        with get_db() as conn:
            cursor = conn.cursor()
            for model_meta in active_models:
                bundle = ModelRegistry.load_bundle(model_meta["id"])
                model = bundle["model"]
                preprocessor = bundle["preprocessor"]
                expected_features = preprocessor.feature_columns

                # Validate compatibility for this model
                is_compat, missing_cols = ModelRegistry.validate_feature_compatibility(bundle, list(df_features.columns))
                if not is_compat:
                    # Skip this model if incompatible
                    continue

                # Preprocess features
                try:
                    X_trans = preprocessor.transform(df_features)
                except Exception as e:
                    # Skip this model on preprocessing error
                    continue

                # Prediction
                try:
                    preds = model.predict(X_trans)
                except Exception:
                    continue

                # Probabilities
                prob_anomaly = None
                if hasattr(model, "predict_proba"):
                    try:
                        probs = model.predict_proba(X_trans)
                        if probs is not None and len(probs) > 0:
                            prob_anomaly = probs[:, 1] if probs.shape[1] > 1 else probs[:, 0]
                    except Exception:
                        prob_anomaly = None

                for i, (record, feat_dict, pred) in enumerate(zip(parsed_records, extracted_features_list, preds)):
                    pred_int = int(pred) if pred is not None else None
                    prob_val = None
                    if prob_anomaly is not None:
                        try:
                            prob_val = round(float(prob_anomaly[i]), 4)
                        except Exception:
                            prob_val = None
                    # Classification
                    cls_policy = policy or RiskClassificationPolicy()
                    category = cls_policy.classify(probability=prob_val, original_prediction=pred_int)
                    conf_val = cls_policy.calculate_confidence(probability=prob_val)
                    is_anomaly_flag = 1 if category == "Anomalous" else 0

                    if category == "Normal":
                        normal_count += 1
                    elif category == "Medium":
                        medium_count += 1
                    elif category == "Anomalous":
                        anomalous_count += 1
                    else:
                        unclassified_count += 1

                    pred_id = f"pred_{uuid.uuid4().hex[:12]}"

                    # SHAP
                    shap_data = None
                    if compute_shap:
                        try:
                            shap_data = ShapExplainabilityEngine.explain_instance(
                                model=model,
                                transformed_row=X_trans[i],
                                feature_names=preprocessor.transformed_feature_names,
                                algorithm=model_meta["algorithm"]
                            )
                        except Exception as se:
                            shap_data = {"available": False, "error": str(se), "contributions": []}

                    explanation_obj = cls_policy.build_explanation(
                        record=record,
                        features=feat_dict,
                        category=category,
                        probability=prob_val,
                        confidence=conf_val,
                        original_prediction=pred_int,
                        shap_data=shap_data,
                        model_meta=model_meta
                    )
                    raw_msg = record.get("message") or record.get("raw", "")
                    log_lvl = cls_policy._decode_log_level(record.get("severity"))

                    cursor.execute(
                        """INSERT INTO predictions (
                            id, batch_id, model_id, model_name, model_version,
                            raw_log, parsed_fields_json, features_json,
                            prediction, probability, is_anomaly, category,
                            risk_score, confidence, explanation_summary,
                            observed_facts_json, model_explanation_json, security_interpretation,
                            shap_values_json, timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            pred_id,
                            batch_uid,
                            model_meta["id"],
                            model_meta["name"],
                            model_meta["version"],
                            record.get("raw", ""),
                            json.dumps(record),
                            json.dumps(feat_dict),
                            pred_int,
                            prob_val,
                            is_anomaly_flag,
                            category,
                            prob_val,
                            conf_val,
                            explanation_obj["summary"],
                            json.dumps(explanation_obj["observed_facts"]),
                            json.dumps(explanation_obj["model_explanation"]),
                            explanation_obj["security_interpretation"],
                            json.dumps(shap_data) if shap_data else None,
                            record.get("timestamp") or now_ts
                        )
                    )

                    all_results.append({
                        "id": pred_id,
                        "raw_log": record.get("raw", ""),
                        "timestamp": record.get("timestamp") or now_ts,
                        "hostname": record.get("hostname") or "localhost",
                        "app_name": record.get("service") or "system",
                        "service": record.get("service") or "system",
                        "log_level": log_lvl,
                        "severity": record.get("severity"),
                        "message": raw_msg,
                        "classification": category,
                        "category": category,
                        "prediction": pred_int,
                        "is_anomaly": bool(is_anomaly_flag),
                        "probability": prob_val,
                        "risk_score": prob_val,
                        "confidence": conf_val,
                        "explanation_summary": explanation_obj["summary"],
                        "observed_facts": explanation_obj["observed_facts"],
                        "model_explanation": explanation_obj["model_explanation"],
                        "security_interpretation": explanation_obj["security_interpretation"],
                        "shap": shap_data,
                        "model_id": model_meta["id"],
                        "model_name": model_meta["name"],
                        "model_version": model_meta["version"]
                    })
        total_all = len(all_results)
        total_classified = normal_count + medium_count + anomalous_count
        return {
            "success": True,
            "has_active_model": True,
            "batch_id": batch_uid,
            "model": {"active_models": [m["id"] for m in active_models]},
            "total_processed": total_all,
            "normal_count": normal_count,
            "medium_count": medium_count,
            "anomalous_count": anomalous_count,
            "unclassified_count": unclassified_count,
            "normal_percentage": round((normal_count / total_classified) * 100, 2) if total_classified > 0 else 0.0,
            "medium_percentage": round((medium_count / total_classified) * 100, 2) if total_classified > 0 else 0.0,
            "anomalous_percentage": round((anomalous_count / total_classified) * 100, 2) if total_classified > 0 else 0.0,
            "unclassified_percentage": round((unclassified_count / total_all) * 100, 2) if total_all > 0 else 0.0,
            "results": all_results
        }

        # Handle No Active Model: Clean error unless unclassified processing explicitly allowed
        if not active_model_meta:
            if not allow_unclassified:
                return {
                    "success": False,
                    "error": "No active model found. Please train and activate a model in the Model Registry before running inference.",
                    "total_processed": 0,
                    "normal_count": 0,
                    "medium_count": 0,
                    "anomalous_count": 0,
                    "unclassified_count": 0,
                    "results": []
                }

            cls_policy = policy or RiskClassificationPolicy()
            results = []
            with get_db() as conn:
                cursor = conn.cursor()
                for record, feat_dict in zip(parsed_records, extracted_features_list):
                    pred_id = f"pred_{uuid.uuid4().hex[:12]}"
                    category = "Unclassified"
                    raw_msg = record.get("message") or record.get("raw", "")
                    explanation_obj = cls_policy.build_explanation(
                        record=record,
                        features=feat_dict,
                        category=category,
                        probability=None,
                        confidence=None,
                        original_prediction=None,
                        shap_data=None,
                        model_meta=None
                    )
                    log_lvl = cls_policy._decode_log_level(record.get("severity"))

                    cursor.execute(
                        """INSERT INTO predictions (
                            id, batch_id, model_id, model_name, model_version,
                            raw_log, parsed_fields_json, features_json,
                            prediction, probability, is_anomaly, category,
                            risk_score, confidence, explanation_summary,
                            observed_facts_json, model_explanation_json, security_interpretation,
                            shap_values_json, timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            pred_id,
                            batch_uid,
                            "unclassified",
                            "None",
                            "N/A",
                            record.get("raw", ""),
                            json.dumps(record),
                            json.dumps(feat_dict),
                            -1,
                            None,
                            0,
                            category,
                            None,
                            None,
                            explanation_obj["summary"],
                            json.dumps(explanation_obj["observed_facts"]),
                            json.dumps(explanation_obj["model_explanation"]),
                            explanation_obj["security_interpretation"],
                            None,
                            record.get("timestamp") or now_ts
                        )
                    )

                    results.append({
                        "id": pred_id,
                        "raw_log": record.get("raw", ""),
                        "timestamp": record.get("timestamp") or now_ts,
                        "hostname": record.get("hostname") or "localhost",
                        "app_name": record.get("service") or "system",
                        "service": record.get("service") or "system",
                        "log_level": log_lvl,
                        "severity": record.get("severity"),
                        "message": raw_msg,
                        "classification": category,
                        "category": category,
                        "prediction": None,
                        "is_anomaly": False,
                        "probability": None,
                        "risk_score": None,
                        "confidence": None,
                        "explanation_summary": explanation_obj["summary"],
                        "observed_facts": explanation_obj["observed_facts"],
                        "model_explanation": explanation_obj["model_explanation"],
                        "security_interpretation": explanation_obj["security_interpretation"],
                        "shap": None
                    })

            return {
                "success": True,
                "has_active_model": False,
                "batch_id": batch_uid,
                "model": None,
                "total_processed": len(results),
                "normal_count": 0,
                "medium_count": 0,
                "anomalous_count": 0,
                "unclassified_count": len(results),
                "normal_percentage": 0.0,
                "medium_percentage": 0.0,
                "anomalous_percentage": 0.0,
                "unclassified_percentage": 100.0,
                "results": results
            }

        bundle = ModelRegistry.load_bundle(active_model_meta["id"])
        model = bundle["model"]
        preprocessor = bundle["preprocessor"]
        expected_features = preprocessor.feature_columns

        # Setup Classification Policy
        if policy:
            cls_policy = policy
        else:
            model_policy_info = bundle.get("metrics", {}).get("classification_policy", {})
            t_norm = model_policy_info.get("threshold_normal", RiskClassificationPolicy.DEFAULT_THRESHOLD_NORMAL)
            t_anom = model_policy_info.get("threshold_anomaly", RiskClassificationPolicy.DEFAULT_THRESHOLD_ANOMALY)
            try:
                cls_policy = RiskClassificationPolicy(threshold_normal=t_norm, threshold_anomaly=t_anom)
            except Exception:
                cls_policy = RiskClassificationPolicy()

        df_features = pd.DataFrame(extracted_features_list)

        # Validate feature compatibility
        is_compat, missing_cols = ModelRegistry.validate_feature_compatibility(bundle, list(df_features.columns))
        if not is_compat:
            return {
                "success": False,
                "error": f"Incoming log features are incompatible with active model '{active_model_meta['name']}'. Missing features: {missing_cols}",
                "expected_features": expected_features,
                "extracted_features": list(df_features.columns),
                "total_processed": 0,
                "results": []
            }

        # Preprocess features
        try:
            X_trans = preprocessor.transform(df_features)
        except Exception as e:
            return {
                "success": False,
                "error": f"Preprocessing failed: {str(e)}",
                "total_processed": 0,
                "results": []
            }

        # Model Prediction
        try:
            preds = model.predict(X_trans)
        except Exception as e:
            return {
                "success": False,
                "error": f"Model prediction failed: {str(e)}",
                "total_processed": 0,
                "results": []
            }

        # Model Probabilities (Check if supported)
        prob_anomaly = None
        has_proba = hasattr(model, "predict_proba")
        if has_proba:
            try:
                probs = model.predict_proba(X_trans)
                if probs is not None and len(probs) > 0:
                    prob_anomaly = probs[:, 1] if probs.shape[1] > 1 else probs[:, 0]
            except Exception:
                prob_anomaly = None

        results = []
        normal_count = 0
        medium_count = 0
        anomalous_count = 0
        unclassified_count = 0

        # Save to database
        with get_db() as conn:
            cursor = conn.cursor()
            for i, (record, feat_dict, pred) in enumerate(zip(parsed_records, extracted_features_list, preds)):
                pred_int = int(pred) if pred is not None else None
                
                # Check if probability exists for this record
                prob_val = None
                if prob_anomaly is not None:
                    try:
                        prob_val = round(float(prob_anomaly[i]), 4)
                    except Exception:
                        prob_val = None

                # Determine 3-level classification category
                category = cls_policy.classify(probability=prob_val, original_prediction=pred_int)
                conf_val = cls_policy.calculate_confidence(probability=prob_val)
                is_anomaly_flag = 1 if category == "Anomalous" else 0

                if category == "Normal":
                    normal_count += 1
                elif category == "Medium":
                    medium_count += 1
                elif category == "Anomalous":
                    anomalous_count += 1
                else:
                    unclassified_count += 1

                pred_id = f"pred_{uuid.uuid4().hex[:12]}"

                # Compute SHAP explanation if requested
                shap_data = None
                if compute_shap:
                    try:
                        shap_data = ShapExplainabilityEngine.explain_instance(
                            model=model,
                            transformed_row=X_trans[i],
                            feature_names=preprocessor.transformed_feature_names,
                            algorithm=active_model_meta["algorithm"]
                        )
                    except Exception as e:
                        shap_data = {"available": False, "error": str(e), "contributions": []}

                explanation_obj = cls_policy.build_explanation(
                    record=record,
                    features=feat_dict,
                    category=category,
                    probability=prob_val,
                    confidence=conf_val,
                    original_prediction=pred_int,
                    shap_data=shap_data,
                    model_meta=active_model_meta
                )

                raw_msg = record.get("message") or record.get("raw", "")
                log_lvl = cls_policy._decode_log_level(record.get("severity"))

                cursor.execute(
                    """INSERT INTO predictions (
                        id, batch_id, model_id, model_name, model_version,
                        raw_log, parsed_fields_json, features_json,
                        prediction, probability, is_anomaly, category,
                        risk_score, confidence, explanation_summary,
                        observed_facts_json, model_explanation_json, security_interpretation,
                        shap_values_json, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        pred_id,
                        batch_uid,
                        active_model_meta["id"],
                        active_model_meta["name"],
                        active_model_meta["version"],
                        record.get("raw", ""),
                        json.dumps(record),
                        json.dumps(feat_dict),
                        pred_int,
                        prob_val,
                        is_anomaly_flag,
                        category,
                        prob_val,
                        conf_val,
                        explanation_obj["summary"],
                        json.dumps(explanation_obj["observed_facts"]),
                        json.dumps(explanation_obj["model_explanation"]),
                        explanation_obj["security_interpretation"],
                        json.dumps(shap_data) if shap_data else None,
                        record.get("timestamp") or now_ts
                    )
                )

                results.append({
                    "id": pred_id,
                    "raw_log": record.get("raw", ""),
                    "timestamp": record.get("timestamp") or now_ts,
                    "hostname": record.get("hostname") or "localhost",
                    "app_name": record.get("service") or "system",
                    "service": record.get("service") or "system",
                    "log_level": log_lvl,
                    "severity": record.get("severity"),
                    "message": raw_msg,
                    "classification": category,
                    "category": category,
                    "prediction": pred_int,
                    "is_anomaly": bool(is_anomaly_flag),
                    "probability": prob_val,
                    "risk_score": prob_val,
                    "confidence": conf_val,
                    "explanation_summary": explanation_obj["summary"],
                    "observed_facts": explanation_obj["observed_facts"],
                    "model_explanation": explanation_obj["model_explanation"],
                    "security_interpretation": explanation_obj["security_interpretation"],
                    "shap": shap_data
                })

        total_classified = normal_count + medium_count + anomalous_count
        total_all = len(results)

        return {
            "success": True,
            "has_active_model": True,
            "batch_id": batch_uid,
            "model": {
                "id": active_model_meta["id"],
                "name": active_model_meta["name"],
                "algorithm": active_model_meta["algorithm"],
                "version": active_model_meta["version"]
            },
            "total_processed": total_all,
            "normal_count": normal_count,
            "medium_count": medium_count,
            "anomalous_count": anomalous_count,
            "unclassified_count": unclassified_count,
            "normal_percentage": round((normal_count / total_classified) * 100, 2) if total_classified > 0 else 0.0,
            "medium_percentage": round((medium_count / total_classified) * 100, 2) if total_classified > 0 else 0.0,
            "anomalous_percentage": round((anomalous_count / total_classified) * 100, 2) if total_classified > 0 else 0.0,
            "unclassified_percentage": round((unclassified_count / total_all) * 100, 2) if total_all > 0 else 0.0,
            "results": results
        }

    @classmethod
    def process_windows_events(
        cls,
        events: List[Dict[str, Any]],
        compute_shap: bool = True,
        policy: Optional[RiskClassificationPolicy] = None
    ) -> Dict[str, Any]:
        """Process real Windows Event Log entries through ML inference and persistence."""
        if not events:
            return {"success": True, "processed": 0, "inserted": 0}

        now_ts = datetime.utcnow().isoformat()
        active_model_meta = ModelRegistry.get_active_model()
        cls_policy = policy or RiskClassificationPolicy()

        bundle = None
        model = None
        preprocessor = None
        is_compatible = False
        incompat_reason = ""

        if active_model_meta:
            try:
                bundle = ModelRegistry.load_bundle(active_model_meta["id"])
                model = bundle["model"]
                preprocessor = bundle["preprocessor"]
                # Test compatibility against extracted features
                sample_record = {
                    "raw": events[0].get("raw", ""),
                    "timestamp": events[0].get("timestamp"),
                    "hostname": events[0].get("computer", "localhost"),
                    "service": events[0].get("provider", "system"),
                    "severity": events[0].get("severity", 6),
                    "message": events[0].get("message", "")
                }
                sample_feat = LogParser.extract_features(sample_record)
                is_compatible, missing = ModelRegistry.validate_feature_compatibility(bundle, list(sample_feat.keys()))
                if not is_compatible:
                    incompat_reason = f"Active model '{active_model_meta['name']}' expects features {missing[:3]}, which are incompatible with collected Windows events."
            except Exception as e:
                is_compatible = False
                incompat_reason = f"Active model failed to load for inference: {str(e)}"
        else:
            incompat_reason = "No active ML model loaded in Model Registry."

        inserted_count = 0
        with get_db() as conn:
            cursor = conn.cursor()
            for event in events:
                raw_msg = str(event.get("message") or "")
                timestamp = event.get("timestamp") or now_ts
                computer = event.get("computer") or "localhost"
                provider = event.get("provider") or "system"
                channel = event.get("channel") or "System"
                record_id = event.get("record_id")
                event_id = event.get("event_id")
                sev_code = event.get("severity", 6)
                sev_label = event.get("severity_label") or cls_policy._decode_log_level(sev_code)
                raw_log = event.get("raw") or f"{timestamp} {computer} {provider}[{event_id}]: {raw_msg}"

                record = {
                    "raw": raw_log,
                    "timestamp": timestamp,
                    "hostname": computer,
                    "service": provider,
                    "channel": channel,
                    "record_id": record_id,
                    "event_id": event_id,
                    "severity": sev_code,
                    "severity_label": sev_label,
                    "message": raw_msg,
                    "source_ip": None,
                    "username": event.get("user_id")
                }
                feat_dict = LogParser.extract_features(record)

                pred_id = f"win_{uuid.uuid4().hex[:12]}"
                category = "Unclassified"
                pred_int = None
                prob_val = None
                conf_val = None
                is_anomaly_flag = 0
                shap_data = None

                if is_compatible and model and preprocessor:
                    try:
                        df_single = pd.DataFrame([feat_dict])
                        X_single = preprocessor.transform(df_single)
                        pred = model.predict(X_single)[0]
                        pred_int = int(pred) if pred is not None else None

                        if hasattr(model, "predict_proba"):
                            probs = model.predict_proba(X_single)
                            if probs is not None and len(probs) > 0:
                                prob_val = round(float(probs[0, 1] if probs.shape[1] > 1 else probs[0, 0]), 4)

                        category = cls_policy.classify(probability=prob_val, original_prediction=pred_int)
                        conf_val = cls_policy.calculate_confidence(probability=prob_val)
                        is_anomaly_flag = 1 if category == "Anomalous" else 0

                        if compute_shap:
                            try:
                                shap_data = ShapExplainabilityEngine.explain_instance(
                                    model=model,
                                    transformed_row=X_single[0],
                                    feature_names=preprocessor.transformed_feature_names,
                                    algorithm=active_model_meta["algorithm"]
                                )
                            except Exception as se:
                                shap_data = {"available": False, "error": str(se), "contributions": []}
                    except Exception as err:
                        category = "Unclassified"
                        incompat_reason = f"Prediction error: {str(err)}"

                # Observed facts
                observed_facts = {
                    "timestamp": timestamp,
                    "hostname": computer,
                    "application_name": provider,
                    "channel": channel,
                    "event_id": event_id,
                    "record_id": record_id,
                    "severity_label": sev_label,
                    "raw_severity_code": sev_code,
                    "message_length": len(raw_msg),
                    "detected_user": event.get("user_id"),
                    "process_id": event.get("pid"),
                    "has_error_flag": bool(feat_dict.get("has_error", 0)),
                    "has_auth_flag": bool(feat_dict.get("has_auth", 0)),
                    "has_failed_auth_flag": bool(feat_dict.get("has_failed_auth", 0)),
                    "has_warning_flag": bool(feat_dict.get("has_warning", 0))
                }

                if category == "Unclassified":
                    summary = incompat_reason or "Unclassified: No compatible model active."
                    model_explanation = {
                        "category": "Unclassified",
                        "reason": summary,
                        "active_model": active_model_meta["name"] if active_model_meta else None
                    }
                    security_interpretation = "Event collected directly from Windows Event Log. Automated threat classification requires an active, compatible trained model."
                else:
                    explanation_obj = cls_policy.build_explanation(
                        record=record,
                        features=feat_dict,
                        category=category,
                        probability=prob_val,
                        confidence=conf_val,
                        original_prediction=pred_int,
                        shap_data=shap_data,
                        model_meta=active_model_meta
                    )
                    summary = explanation_obj["summary"]
                    model_explanation = explanation_obj["model_explanation"]
                    security_interpretation = explanation_obj["security_interpretation"]

                cursor.execute(
                    """INSERT OR IGNORE INTO predictions (
                        id, batch_id, model_id, model_name, model_version,
                        raw_log, parsed_fields_json, features_json,
                        prediction, probability, is_anomaly, category,
                        risk_score, confidence, explanation_summary,
                        observed_facts_json, model_explanation_json, security_interpretation,
                        shap_values_json, timestamp,
                        channel, record_id, event_id, provider, severity_label
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        pred_id,
                        f"win_{channel.lower()}",
                        active_model_meta["id"] if (active_model_meta and is_compatible) else "unclassified",
                        active_model_meta["name"] if (active_model_meta and is_compatible) else "Windows Live Ingestion",
                        active_model_meta["version"] if (active_model_meta and is_compatible) else "1.0",
                        raw_log,
                        json.dumps(record),
                        json.dumps(feat_dict),
                        pred_int if pred_int is not None else -1,
                        prob_val,
                        is_anomaly_flag,
                        category,
                        prob_val,
                        conf_val,
                        summary,
                        json.dumps(observed_facts),
                        json.dumps(model_explanation),
                        security_interpretation,
                        json.dumps(shap_data) if shap_data else None,
                        timestamp,
                        channel,
                        record_id,
                        event_id,
                        provider,
                        sev_label
                    )
                )
                if cursor.rowcount > 0:
                    inserted_count += 1

        return {
            "success": True,
            "processed": len(events),
            "inserted": inserted_count
        }
