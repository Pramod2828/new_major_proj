import numpy as np
from typing import Dict, Any, List, Optional
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
    auc
)

class EvaluationMetrics:
    """Evaluates binary anomaly detection models where Anomaly=1 (positive class) and Normal=0."""

    @classmethod
    def evaluate(
        cls,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Compute comprehensive evaluation metrics for binary classification.
        
        Args:
            y_true: True binary labels (0=Normal, 1=Anomaly)
            y_pred: Predicted binary labels (0=Normal, 1=Anomaly)
            y_prob: Predicted probability for positive class (Anomaly=1)
            
        Returns:
            Dictionary containing metrics, confusion matrix, rates, and curve points.
        """
        y_true = np.asarray(y_true, dtype=int)
        y_pred = np.asarray(y_pred, dtype=int)

        # Basic counts
        total_samples = len(y_true)
        actual_anomalies = int(np.sum(y_true == 1))
        actual_normals = int(np.sum(y_true == 0))

        # Confusion Matrix [[TN, FP], [FN, TP]]
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = [int(v) for v in cm.ravel()]

        # Rates
        acc = float(accuracy_score(y_true, y_pred))
        # Zero division safe metrics
        prec = float(precision_score(y_true, y_pred, zero_division=0))
        rec = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        fpr = round(fp / (fp + tn), 4) if (fp + tn) > 0 else 0.0
        fnr = round(fn / (fn + tp), 4) if (fn + tp) > 0 else 0.0
        specificity = round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0.0

        # Probabilities & Curves
        roc_auc_val = None
        pr_auc_val = None
        roc_curve_points = []
        pr_curve_points = []

        if y_prob is not None and len(np.unique(y_true)) > 1:
            try:
                # Ensure 1D probabilities for class 1
                y_prob_1d = np.asarray(y_prob, dtype=float)
                if y_prob_1d.ndim > 1:
                    y_prob_1d = y_prob_1d[:, 1]

                roc_auc_val = round(float(roc_auc_score(y_true, y_prob_1d)), 4)

                # ROC Curve points (downsampled to max 25 points for efficient JSON transfer)
                fpr_vals, tpr_vals, _ = roc_curve(y_true, y_prob_1d)
                roc_curve_points = cls._downsample_points(fpr_vals, tpr_vals, max_points=25, x_name="fpr", y_name="tpr")

                # PR Curve points
                p_vals, r_vals, _ = precision_recall_curve(y_true, y_prob_1d)
                pr_auc_val = round(float(auc(r_vals, p_vals)), 4)
                pr_curve_points = cls._downsample_points(r_vals, p_vals, max_points=25, x_name="recall", y_name="precision")
            except Exception:
                pass

        return {
            "total_samples": total_samples,
            "actual_anomalies": actual_anomalies,
            "actual_normals": actual_normals,
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "false_positive_rate": fpr,
            "false_negative_rate": fnr,
            "specificity": specificity,
            "roc_auc": roc_auc_val,
            "pr_auc": pr_auc_val,
            "confusion_matrix": {
                "tn": tn,
                "fp": fp,
                "fn": fn,
                "tp": tp,
                "matrix": [[tn, fp], [fn, tp]]
            },
            "roc_curve": roc_curve_points,
            "pr_curve": pr_curve_points,
            "positive_label_definition": "Anomaly (1)",
            "negative_label_definition": "Normal (0)"
        }

    @staticmethod
    def _downsample_points(x_vals, y_vals, max_points=25, x_name="x", y_name="y") -> List[Dict[str, float]]:
        """Downsample curve points for frontend charts."""
        n = len(x_vals)
        if n <= max_points:
            indices = list(range(n))
        else:
            indices = np.linspace(0, n - 1, max_points, dtype=int).tolist()

        points = []
        for idx in indices:
            points.append({
                x_name: round(float(x_vals[idx]), 4),
                y_name: round(float(y_vals[idx]), 4)
            })
        return points
