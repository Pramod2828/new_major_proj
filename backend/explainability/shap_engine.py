import sys
import types
from typing import Dict, Any, List, Optional
import numpy as np

# Ensure torch mock is available to avoid torch c10.dll crash on Windows
if "torch" not in sys.modules:
    try:
        import torch  # noqa: F401
    except (ImportError, OSError):
        m = types.ModuleType("torch")
        m.Tensor = type("Tensor", (), {})
        sys.modules["torch"] = m

import shap
import shap.explainers._tree as _tree_mod

# Compatibility patch for XGBoost 2.0+/3.0+ base_score string formatting in SHAP
try:
    if hasattr(_tree_mod, "decode_ubjson_buffer"):
        _orig_decode = _tree_mod.decode_ubjson_buffer

        def _patched_decode(fd):
            res = _orig_decode(fd)
            try:
                if isinstance(res, dict) and "learner" in res:
                    lmp = res["learner"].get("learner_model_param", {})
                    bs = lmp.get("base_score")
                    if isinstance(bs, str) and bs.startswith("[") and bs.endswith("]"):
                        lmp["base_score"] = bs.strip("[]")
            except Exception:
                pass
            return res

        _tree_mod.decode_ubjson_buffer = _patched_decode

    if hasattr(_tree_mod, "XGBTreeModelLoader") and hasattr(_tree_mod.XGBTreeModelLoader, "read_xgb_params"):
        _orig_read_xgb_params = _tree_mod.XGBTreeModelLoader.read_xgb_params

        def _patched_read_xgb_params(xgb_model):
            p = _orig_read_xgb_params(xgb_model)
            try:
                bs = p.get("learner_model_param", {}).get("base_score")
                if isinstance(bs, str) and bs.startswith("[") and bs.endswith("]"):
                    p["learner_model_param"]["base_score"] = bs.strip("[]")
            except Exception:
                pass
            return p

        _tree_mod.XGBTreeModelLoader.read_xgb_params = staticmethod(_patched_read_xgb_params)
except Exception:
    pass

class ShapExplainabilityEngine:
    """SHAP explainability engine for tree-based models (Random Forest and XGBoost)."""

    @classmethod
    def explain_instance(
        cls,
        model,
        transformed_row: np.ndarray,
        feature_names: List[str],
        algorithm: str = "random_forest"
    ) -> Dict[str, Any]:
        """Generate SHAP explanation for a single prediction row.
        
        Args:
            model: Trained estimator (RandomForestClassifier or XGBClassifier)
            transformed_row: 1D or 2D array of transformed features (shape: (1, n_features))
            feature_names: Exact list of feature names matching transformed_row
            algorithm: 'random_forest' or 'xgboost'
            
        Returns:
            Dict containing base_value, feature_contributions, and prediction_impact.
        """
        row_2d = np.atleast_2d(transformed_row)
        n_features = row_2d.shape[1]

        if len(feature_names) != n_features:
            feature_names = [f"feat_{i}" for i in range(n_features)]

        try:
            explainer = shap.TreeExplainer(model)
            shap_output = explainer.shap_values(row_2d)

            # Handle base value
            base_val = explainer.expected_value
            if isinstance(base_val, (list, np.ndarray)):
                # If multiclass/binary list, take class 1 (Anomaly)
                base_val = float(base_val[1]) if len(base_val) > 1 else float(base_val[0])
            else:
                base_val = float(base_val)

            # Extract SHAP values for class 1 (Anomaly)
            if isinstance(shap_output, list):
                # RF classification returns list [class0_vals, class1_vals]
                class1_vals = shap_output[1][0] if len(shap_output) > 1 else shap_output[0][0]
            elif isinstance(shap_output, np.ndarray):
                if shap_output.ndim == 3:
                    # (samples, features, classes)
                    class1_vals = shap_output[0, :, 1]
                elif shap_output.ndim == 2:
                    # (samples, features)
                    class1_vals = shap_output[0]
                else:
                    class1_vals = shap_output
            else:
                raise ValueError("Unexpected SHAP output structure")

            # Build contributions list
            contributions = []
            for name, val, raw_fval in zip(feature_names, class1_vals, row_2d[0]):
                val_flt = round(float(val), 5)
                contributions.append({
                    "feature": name,
                    "contribution": val_flt,
                    "abs_contribution": abs(val_flt),
                    "feature_value": round(float(raw_fval), 4) if np.issubdtype(type(raw_fval), np.number) else str(raw_fval),
                    "direction": "anomaly" if val_flt > 0 else ("normal" if val_flt < 0 else "neutral")
                })

            # Sort by absolute impact (highest first)
            contributions.sort(key=lambda x: x["abs_contribution"], reverse=True)

            return {
                "available": True,
                "base_value": round(base_val, 4),
                "contributions": contributions,
                "top_anomaly_drivers": [c for c in contributions if c["direction"] == "anomaly"][:5],
                "top_normal_drivers": [c for c in contributions if c["direction"] == "normal"][:5],
                "error": None
            }
        except Exception as e:
            return {
                "available": False,
                "base_value": None,
                "contributions": [],
                "top_anomaly_drivers": [],
                "top_normal_drivers": [],
                "error": f"SHAP calculation error: {str(e)}"
            }

    @classmethod
    def compute_global_importance(
        cls,
        model,
        transformed_sample: np.ndarray,
        feature_names: List[str]
    ) -> List[Dict[str, Any]]:
        """Compute mean absolute SHAP values across a batch of samples."""
        sample_2d = np.atleast_2d(transformed_sample)
        if len(sample_2d) > 100:
            sample_2d = sample_2d[:100]  # Cap at 100 for fast response

        try:
            explainer = shap.TreeExplainer(model)
            shap_output = explainer.shap_values(sample_2d)

            if isinstance(shap_output, list):
                class1_vals = shap_output[1] if len(shap_output) > 1 else shap_output[0]
            elif isinstance(shap_output, np.ndarray):
                if shap_output.ndim == 3:
                    class1_vals = shap_output[:, :, 1]
                else:
                    class1_vals = shap_output
            else:
                return []

            mean_abs = np.mean(np.abs(class1_vals), axis=0)
            if len(feature_names) != len(mean_abs):
                feature_names = [f"feat_{i}" for i in range(len(mean_abs))]

            global_ranking = []
            for name, score in zip(feature_names, mean_abs):
                global_ranking.append({
                    "feature": name,
                    "mean_abs_shap": round(float(score), 5)
                })

            global_ranking.sort(key=lambda x: x["mean_abs_shap"], reverse=True)
            return global_ranking
        except Exception:
            return []
