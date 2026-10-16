import math
from typing import Dict, Any, List, Optional, Tuple

class RiskClassificationPolicy:
    """Configurable three-level risk classification policy with transparent decision layers."""

    # Default calibrated threshold values
    DEFAULT_THRESHOLD_NORMAL: float = 0.30
    DEFAULT_THRESHOLD_ANOMALY: float = 0.70

    def __init__(
        self,
        threshold_normal: float = DEFAULT_THRESHOLD_NORMAL,
        threshold_anomaly: float = DEFAULT_THRESHOLD_ANOMALY,
        policy_name: str = "Configured Probability Threshold Policy"
    ):
        if not (0.0 <= threshold_normal < threshold_anomaly <= 1.0):
            raise ValueError(
                f"Invalid policy thresholds: 0.0 <= threshold_normal ({threshold_normal}) "
                f"< threshold_anomaly ({threshold_anomaly}) <= 1.0 is required."
            )
        self.threshold_normal = round(float(threshold_normal), 4)
        self.threshold_anomaly = round(float(threshold_anomaly), 4)
        self.policy_name = policy_name

    def classify(
        self,
        probability: Optional[float],
        original_prediction: Optional[int] = None
    ) -> str:
        """Determine three-level risk category from model probability.
        
        Returns:
            'Normal', 'Medium', 'Anomalous', or 'Unclassified'
        """
        if probability is None or not isinstance(probability, (int, float)) or math.isnan(probability):
            return "Unclassified"

        prob = float(probability)
        if prob < self.threshold_normal:
            return "Normal"
        elif prob < self.threshold_anomaly:
            return "Medium"
        else:
            return "Anomalous"

    def calculate_confidence(self, probability: Optional[float]) -> Optional[float]:
        """Calculate decision confidence score only when supported.
        
        Returns confidence in [0.0, 1.0], or None if unsupported.
        For binary probabilities, confidence represents distance from ambiguous center (0.5).
        """
        if probability is None or not isinstance(probability, (int, float)) or math.isnan(probability):
            return None
        prob = float(probability)
        # Distance from neutral center 0.5 scaled to [0, 1]
        conf = abs(prob - 0.5) * 2.0
        return round(conf, 4)

    def build_explanation(
        self,
        record: Dict[str, Any],
        features: Dict[str, Any],
        category: str,
        probability: Optional[float],
        confidence: Optional[float],
        original_prediction: Optional[int],
        shap_data: Optional[Dict[str, Any]] = None,
        model_meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Construct structured explanation separating observed facts, model explanation, and security interpretations."""
        
        # 1. Observed Facts
        raw_msg = str(record.get("message") or record.get("raw") or "")
        observed_facts = {
            "timestamp": record.get("timestamp") or "N/A",
            "hostname": record.get("hostname") or "localhost",
            "application_name": record.get("service") or "system",
            "log_level": self._decode_log_level(record.get("severity")),
            "raw_severity_code": record.get("severity"),
            "message_length": len(raw_msg),
            "entropy": features.get("entropy", 0.0),
            "token_count": features.get("token_count", 0),
            "detected_source_ip": record.get("source_ip") or features.get("source_ip"),
            "detected_user": record.get("username") or features.get("username"),
            "has_error_flag": bool(features.get("has_error", 0)),
            "has_auth_flag": bool(features.get("has_auth", 0)),
            "has_failed_auth_flag": bool(features.get("has_failed_auth", 0)),
            "has_denied_flag": bool(features.get("has_denied", 0)),
            "has_warning_flag": bool(features.get("has_warning", 0))
        }

        # 2. Model Explanation
        prob_pct = f"{round(probability * 100, 1)}%" if probability is not None else "N/A"
        conf_pct = f"{round(confidence * 100, 1)}%" if confidence is not None else "N/A"
        
        top_positive_shap = []
        top_negative_shap = []
        if shap_data and shap_data.get("available") and shap_data.get("contributions"):
            for c in shap_data["contributions"]:
                if c.get("direction") == "anomaly" or c.get("contribution", 0) > 0:
                    top_positive_shap.append(c)
                else:
                    top_negative_shap.append(c)

        if category == "Normal":
            summary = f"Normal operational log (Risk: {prob_pct}) conforming to baseline model patterns."
            rationale = (
                f"Model predicted anomaly probability of {prob_pct}, which is strictly below the Normal risk threshold "
                f"of {round(self.threshold_normal * 100, 1)}%. "
                f"Decision is supported by baseline operational feature values and low error indicators."
            )
            uncertainty_note = "Model confidence is high for operational conformity."
        elif category == "Medium":
            summary = f"Medium/borderline risk event (Risk: {prob_pct}) within uncertainty range [{round(self.threshold_normal * 100, 1)}% - {round(self.threshold_anomaly * 100, 1)}%)."
            rationale = (
                f"Model predicted anomaly probability of {prob_pct}, placing it in the intermediate risk policy band "
                f"[{round(self.threshold_normal * 100, 1)}% - {round(self.threshold_anomaly * 100, 1)}%). "
                f"This indicates a borderline classification where features exhibit mild deviation without meeting definitive anomaly thresholds."
            )
            uncertainty_note = (
                "Classification exhibits moderate uncertainty. Feature contributions push in opposing directions "
                "or exhibit marginal deviation from training baselines."
            )
        elif category == "Anomalous":
            summary = f"High-risk anomaly (Risk: {prob_pct}) exceeding anomaly criteria (≥ {round(self.threshold_anomaly * 100, 1)}%)."
            rationale = (
                f"Model predicted anomaly probability of {prob_pct}, meeting the high-risk anomaly threshold "
                f"of ≥ {round(self.threshold_anomaly * 100, 1)}%. "
                f"Classification is heavily driven by elevated risk indicators and statistical outliers."
            )
            uncertainty_note = "Model confidence is high for anomaly classification."
        else: # Unclassified
            summary = "Unclassified event: Model probability or active classifier unavailable."
            rationale = (
                "A reliable model decision could not be made. "
                "The active classifier either did not output class probabilities, the model is uninitialized, "
                "or incoming log features could not be evaluated against the configured policy."
            )
            uncertainty_note = "Classification cannot be performed without valid model probability outputs."

        model_explanation = {
            "model_name": model_meta.get("name", "N/A") if model_meta else "N/A",
            "algorithm": model_meta.get("algorithm", "N/A") if model_meta else "N/A",
            "model_version": model_meta.get("version", "N/A") if model_meta else "N/A",
            "original_prediction": original_prediction,
            "risk_score_probability": probability,
            "confidence_score": confidence,
            "policy_threshold_normal": self.threshold_normal,
            "policy_threshold_anomaly": self.threshold_anomaly,
            "decision_rationale": rationale,
            "uncertainty_note": uncertainty_note,
            "top_anomaly_drivers": top_positive_shap[:5],
            "top_normal_drivers": top_negative_shap[:5]
        }

        # 3. Possible Security Interpretations
        if category == "Normal":
            sec_interpretation = (
                "Observed log activity matches typical operational baseline patterns. "
                "No indicators of compromise or anomalous execution behaviors were detected in the analyzed features."
            )
        elif category == "Medium":
            sec_interpretation = (
                "Observed event exhibits atypical characteristics (such as elevated entropy, warning severity, or non-standard process activity) "
                "that warrant operational review, but does not meet definitive anomaly criteria. "
                "Recommended operational action: correlate with subsequent session events on host."
            )
        elif category == "Anomalous":
            sec_interpretation = (
                "Observed event significantly deviates from baseline operational models, exhibiting elevated risk indicators "
                "(such as authentication failure patterns or critical service exceptions). "
                "Recommended operational action: investigate host logs, source IP, and related process activity. "
                "Note: Anomaly classification indicates statistical deviation from training baseline, not a confirmed attack."
            )
        else:
            sec_interpretation = (
                "Reliable risk assessment cannot be determined from available model telemetry. "
                "Event is retained in the audit log for manual administrative review."
            )

        return {
            "summary": summary,
            "observed_facts": observed_facts,
            "model_explanation": model_explanation,
            "security_interpretation": sec_interpretation
        }

    @staticmethod
    def _decode_log_level(sev: Optional[Any]) -> str:
        """Decode numerical severity code into standard syslog severity string."""
        if sev is None:
            return "INFO"
        try:
            s = int(sev)
            mapping = {
                0: "EMERGENCY",
                1: "ALERT",
                2: "CRITICAL",
                3: "ERROR",
                4: "WARNING",
                5: "NOTICE",
                6: "INFO",
                7: "DEBUG"
            }
            return mapping.get(s, f"LEVEL_{s}")
        except Exception:
            return str(sev).upper()

    def validate_on_validation_set(
        self,
        y_val: List[int],
        y_probs: List[float]
    ) -> Dict[str, Any]:
        """Validate threshold policy on held-out validation set and evaluate separation."""
        total = len(y_val)
        if total == 0:
            return {
                "validated": False,
                "reason": "Validation set is empty"
            }

        normal_count = 0
        medium_count = 0
        anomalous_count = 0

        normal_true_anomalies = 0
        anomalous_true_anomalies = 0

        for true_label, prob in zip(y_val, y_probs):
            cat = self.classify(prob)
            if cat == "Normal":
                normal_count += 1
                if true_label == 1:
                    normal_true_anomalies += 1
            elif cat == "Medium":
                medium_count += 1
            elif cat == "Anomalous":
                anomalous_count += 1
                if true_label == 1:
                    anomalous_true_anomalies += 1

        return {
            "validated": True,
            "threshold_normal": self.threshold_normal,
            "threshold_anomaly": self.threshold_anomaly,
            "total_validation_samples": total,
            "distribution": {
                "normal_count": normal_count,
                "normal_percent": round((normal_count / total) * 100, 2),
                "medium_count": medium_count,
                "medium_percent": round((medium_count / total) * 100, 2),
                "anomalous_count": anomalous_count,
                "anomalous_percent": round((anomalous_count / total) * 100, 2)
            },
            "anomalous_precision": round(anomalous_true_anomalies / anomalous_count, 4) if anomalous_count > 0 else 0.0,
            "normal_false_negative_rate": round(normal_true_anomalies / normal_count, 4) if normal_count > 0 else 0.0
        }
