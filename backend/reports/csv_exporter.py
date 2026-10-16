import io
import csv
from typing import List, Dict, Any

class CSVExporter:
    """Exports prediction results, risk classifications, and metrics to CSV format."""

    @classmethod
    def export_predictions(cls, predictions: List[Dict[str, Any]]) -> str:
        """Export list of prediction records to CSV string with 3-level categories."""
        output = io.StringIO()
        fieldnames = [
            "id",
            "timestamp",
            "is_anomaly",
            "category",
            "classification",
            "risk_score",
            "confidence",
            "original_prediction",
            "hostname",
            "application_name",
            "severity",
            "explanation_summary",
            "raw_log"
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for p in predictions:
            cat = p.get("category") or ("Anomalous" if p.get("is_anomaly") else "Normal")
            risk = p.get("risk_score") if p.get("risk_score") is not None else p.get("probability")
            row = {
                "id": p.get("id"),
                "timestamp": p.get("timestamp"),
                "category": cat,
                "classification": cat,
                "risk_score": risk,
                "confidence": p.get("confidence"),
                "original_prediction": p.get("prediction"),
                "is_anomaly": 1 if (cat in ("Anomalous", "Anomaly") or p.get("is_anomaly")) else 0,
                "hostname": p.get("hostname") or "localhost",
                "application_name": p.get("app_name") or p.get("service") or "system",
                "severity": p.get("severity"),
                "explanation_summary": p.get("explanation_summary") or "",
                "raw_log": p.get("raw_log")
            }
            writer.writerow(row)

        return output.getvalue()
