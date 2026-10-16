import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from backend.services.inference_service import InferenceService
from backend.services.classification_policy import RiskClassificationPolicy
from backend.models.registry import ModelRegistry
from backend.explainability.shap_engine import ShapExplainabilityEngine
from backend.database.db import query_all, query_one, execute_write

inference_bp = Blueprint("inference", __name__)

@inference_bp.route("/inference/predict-logs", methods=["POST"])
def predict_logs():
    """Run anomaly detection and 3-level classification inference on raw log strings."""
    data = request.get_json() or {}
    logs = data.get("logs", [])
    if not logs:
        # Check if single log was passed
        single_log = data.get("log")
        if single_log:
            logs = [single_log]
        else:
            return jsonify({"error": "No logs provided. Send an array of log lines in 'logs'."}), 400

    compute_shap = bool(data.get("compute_shap", True))
    result = InferenceService.predict_logs(raw_lines=logs, compute_shap=compute_shap)

    if not result.get("success", False):
        return jsonify(result), 400

    return jsonify(result), 200

@inference_bp.route("/inference/predict-file", methods=["POST"])
def predict_file():
    """Upload log file for live analysis."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    content = file.read().decode("utf-8", errors="replace")
    lines = [l.strip() for l in content.splitlines() if l.strip()]

    if not lines:
        return jsonify({"error": "Uploaded log file contains no readable lines."}), 400

    result = InferenceService.predict_logs(raw_lines=lines, compute_shap=True)
    if not result.get("success", False):
        return jsonify(result), 400

    return jsonify(result), 200

@inference_bp.route("/inference/history", methods=["GET"])
def get_history():
    """Search and filter historical predictions across 3 risk categories and time ranges."""
    category = request.args.get("category")
    is_anomaly = request.args.get("is_anomaly")
    model_id = request.args.get("model_id")
    time_range = request.args.get("time_range")
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    query = """
        SELECT id, batch_id, model_name, model_version, raw_log,
               prediction, probability, is_anomaly, category, risk_score, confidence,
               explanation_summary, timestamp
        FROM predictions WHERE 1=1
    """
    params = []

    if category and category.lower() != "all":
        query += " AND category = ?"
        params.append(category)

    if is_anomaly is not None:
        query += " AND is_anomaly = ?"
        params.append(1 if is_anomaly.lower() in ("true", "1") else 0)

    if model_id:
        query += " AND model_id = ?"
        params.append(model_id)

    if time_range:
        now = datetime.utcnow()
        if time_range == "24h":
            cutoff = (now - timedelta(hours=24)).isoformat()
            query += " AND timestamp >= ?"
            params.append(cutoff)
        elif time_range == "7d":
            cutoff = (now - timedelta(days=7)).isoformat()
            query += " AND timestamp >= ?"
            params.append(cutoff)
        elif time_range == "30d":
            cutoff = (now - timedelta(days=30)).isoformat()
            query += " AND timestamp >= ?"
            params.append(cutoff)

    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params_for_records = list(params)
    params_for_records.extend([limit, offset])

    rows = query_all(query, params_for_records)

    # Calculate scope totals
    total = query_one("SELECT COUNT(*) as c FROM predictions")["c"]
    total_normal = query_one("SELECT COUNT(*) as c FROM predictions WHERE category = 'Normal'")["c"]
    total_medium = query_one("SELECT COUNT(*) as c FROM predictions WHERE category = 'Medium'")["c"]
    total_anomalies = query_one("SELECT COUNT(*) as c FROM predictions WHERE category = 'Anomalous'")["c"]
    total_unclassified = query_one("SELECT COUNT(*) as c FROM predictions WHERE category = 'Unclassified' OR category IS NULL")["c"]

    formatted = []
    for r in rows:
        cat = r["category"] or "Unclassified"
        formatted.append({
            "id": r["id"],
            "batch_id": r["batch_id"],
            "model_name": r["model_name"],
            "model_version": r["model_version"],
            "raw_log": r["raw_log"],
            "prediction": r["prediction"],
            "probability": r["probability"],
            "risk_score": r["risk_score"] if r["risk_score"] is not None else r["probability"],
            "confidence": r["confidence"],
            "category": cat,
            "classification": cat,
            "is_anomaly": bool(r["is_anomaly"]),
            "explanation_summary": r["explanation_summary"],
            "timestamp": r["timestamp"]
        })

    return jsonify({
        "total": total,
        "normal_count": total_normal,
        "medium_count": total_medium,
        "anomalous_count": total_anomalies,
        "unclassified_count": total_unclassified,
        "limit": limit,
        "offset": offset,
        "records": formatted
    }), 200

@inference_bp.route("/inference/<pred_id>", methods=["GET"])
def get_prediction_detail(pred_id):
    """Get full prediction record including structured explanations and SHAP attribution."""
    row = query_one("SELECT * FROM predictions WHERE id = ?", (pred_id,))
    if not row:
        return jsonify({"error": "Prediction record not found"}), 404

    cat = row.get("category") or "Unclassified"
    return jsonify({
        "id": row["id"],
        "batch_id": row["batch_id"],
        "model_id": row["model_id"],
        "model_name": row["model_name"],
        "model_version": row["model_version"],
        "raw_log": row["raw_log"],
        "parsed_fields": json.loads(row["parsed_fields_json"]) if row.get("parsed_fields_json") else {},
        "features": json.loads(row["features_json"]) if row.get("features_json") else {},
        "prediction": row["prediction"],
        "probability": row["probability"],
        "risk_score": row["risk_score"] if row.get("risk_score") is not None else row["probability"],
        "confidence": row.get("confidence"),
        "category": cat,
        "classification": cat,
        "is_anomaly": bool(row["is_anomaly"]),
        "explanation_summary": row.get("explanation_summary"),
        "observed_facts": json.loads(row["observed_facts_json"]) if row.get("observed_facts_json") else {},
        "model_explanation": json.loads(row["model_explanation_json"]) if row.get("model_explanation_json") else {},
        "security_interpretation": row.get("security_interpretation"),
        "shap": json.loads(row["shap_values_json"]) if row.get("shap_values_json") else None,
        "timestamp": row["timestamp"]
    }), 200

@inference_bp.route("/models/<model_id>/policy", methods=["GET", "POST"])
def model_classification_policy(model_id):
    """Inspect or update the three-level classification policy thresholds for a model."""
    bundle = ModelRegistry.load_bundle(model_id)
    if not bundle:
        return jsonify({"error": "Model bundle not found"}), 404

    if request.method == "POST":
        data = request.get_json() or {}
        t_norm = data.get("threshold_normal")
        t_anom = data.get("threshold_anomaly")
        try:
            policy = RiskClassificationPolicy(
                threshold_normal=float(t_norm),
                threshold_anomaly=float(t_anom)
            )
        except Exception as e:
            return jsonify({"error": f"Invalid thresholds: {str(e)}"}), 400

        # Update metrics in bundle
        bundle.setdefault("metrics", {})["classification_policy"] = {
            "threshold_normal": policy.threshold_normal,
            "threshold_anomaly": policy.threshold_anomaly,
            "policy_name": policy.policy_name,
            "updated_at": datetime.utcnow().isoformat()
        }
        ModelRegistry.save_model(
            model_wrapper=bundle["model"],
            preprocessor=bundle["preprocessor"],
            metrics=bundle["metrics"],
            dataset_meta={"name": bundle.get("dataset_name")},
            version=bundle.get("version", "1.0")
        )
        return jsonify({
            "message": "Classification policy updated successfully",
            "policy": bundle["metrics"]["classification_policy"]
        }), 200

    # GET
    policy_info = bundle.get("metrics", {}).get("classification_policy", {
        "threshold_normal": RiskClassificationPolicy.DEFAULT_THRESHOLD_NORMAL,
        "threshold_anomaly": RiskClassificationPolicy.DEFAULT_THRESHOLD_ANOMALY,
        "policy_name": "Default 3-Level Risk Classification Policy"
    })
    return jsonify({
        "model_id": model_id,
        "model_name": bundle["name"],
        "policy": policy_info
    }), 200

@inference_bp.route("/models/<model_id>/shap-global", methods=["GET"])
def get_model_global_shap(model_id):
    """Retrieve global feature importance ranking using SHAP."""
    bundle = ModelRegistry.load_bundle(model_id)
    if not bundle:
        return jsonify({"error": "Model bundle not found"}), 404

    native_importances = bundle.get("metrics", {}).get("feature_importances", {})
    feature_names = bundle.get("feature_schema", {}).get("transformed_feature_names", [])

    return jsonify({
        "model_id": model_id,
        "model_name": bundle["name"],
        "algorithm": bundle["algorithm"],
        "feature_names": feature_names,
        "native_importances": native_importances
    }), 200
