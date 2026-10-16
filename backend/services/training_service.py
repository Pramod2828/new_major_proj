import time
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Added import for built-in dataset loading
from backend.training.train_ait_lds import load_dataset as builtin_load_dataset

from backend.dataset.loader import DatasetLoader
from backend.dataset.validator import DatasetValidator
from backend.preprocessing.pipeline import PreprocessingBundle
from backend.models.random_forest.rf_classifier import RandomForestModelWrapper
from backend.models.xgboost.xgb_classifier import XGBoostModelWrapper
from backend.models.registry import ModelRegistry
from backend.evaluation.metrics import EvaluationMetrics
from backend.services.classification_policy import RiskClassificationPolicy
from backend.database.db import query_one, execute_write

class TrainingService:
    """Orchestrates dataset validation, preprocessing, model training, and evaluation."""

    @classmethod
    def train_models(
        cls,
        dataset_id: str,
        algorithms: list = None,
        rf_params: Dict[str, Any] = None,
        xgb_params: Dict[str, Any] = None,
        split_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Train Random Forest and/or XGBoost on approved configured dataset.
        
        Args:
            dataset_id: Identifier of the dataset
            algorithms: List of algorithms to train ('random_forest', 'xgboost')
            rf_params: Hyperparameters for Random Forest
            xgb_params: Hyperparameters for XGBoost
            split_config: Custom split ratios
            
        Returns:
            Dict containing training results, metrics, and registered model IDs.
        """
        algorithms = algorithms or ["random_forest", "xgboost"]
        rf_params = rf_params or {}
        xgb_params = xgb_params or {}

        # 1. Fetch dataset record
        dataset_row = query_one("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
        if not dataset_row:
            raise ValueError(f"Dataset '{dataset_id}' not found.")

        # 2. Fetch dataset config
        config_row = query_one("SELECT * FROM dataset_configs WHERE dataset_id = ?", (dataset_id,))
        if not config_row:
            raise ValueError(f"Dataset '{dataset_id}' has not been configured. Configure target labels and features first.")

        # Parse config
        feature_cols = json.loads(config_row["feature_columns_json"])
        config_dict = {
            "target_column": config_row["target_column"],
            "normal_value": config_row["normal_value"],
            "anomaly_value": config_row["anomaly_value"],
            "feature_columns": feature_cols,
            "train_ratio": float(split_config.get("train_ratio", config_row["train_ratio"])) if split_config else float(config_row["train_ratio"]),
            "val_ratio": float(split_config.get("val_ratio", config_row["val_ratio"])) if split_config else float(config_row["val_ratio"]),
            "test_ratio": float(split_config.get("test_ratio", config_row["test_ratio"])) if split_config else float(config_row["test_ratio"]),
            "stratified": bool(config_row["stratified"])
        }

        # 3. Load dataset
        if dataset_row["file_path"]:
            df, _ = DatasetLoader.load(dataset_row["file_path"])
        else:
            # Built-in dataset: use the built-in loader by dataset name (strip 'builtin_' prefix)
            builtin_name = dataset_row["id"].replace("builtin_", "")
            df, _ = builtin_load_dataset(builtin_name)

        # 4. Validate configuration
        is_valid, errors, warnings = DatasetValidator.validate_configuration(df, config_dict)
        if not is_valid:
            raise ValueError(f"Dataset validation failed: {'; '.join(errors)}")

        # 5. Filter unmapped records & map target
        target_col = config_dict["target_column"]
        norm_val = str(config_dict["normal_value"])
        anom_val = str(config_dict["anomaly_value"])

        # Drop rows where target is missing
        df_clean = df.dropna(subset=[target_col]).copy()
        df_clean["_str_target"] = df_clean[target_col].astype(str)
        # Keep only normal and anomaly rows
        df_clean = df_clean[df_clean["_str_target"].isin([norm_val, anom_val])].copy()

        # Map labels: normal -> 0, anomaly -> 1
        y = (df_clean["_str_target"] == anom_val).astype(int).values
        X = df_clean[feature_cols].copy()

        # 6. Train/Val/Test Split
        test_size = config_dict["test_ratio"]
        val_size = config_dict["val_ratio"]
        train_size = config_dict["train_ratio"]

        # Stratified if classes permit
        strat = y if (config_dict["stratified"] and len(np.unique(y)) > 1 and np.min(np.bincount(y)) >= 2) else None

        # First split into train_val and test
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=test_size, stratify=strat, random_state=42
        )

        # Then split train_val into train and val
        val_relative_ratio = val_size / (train_size + val_size) if (train_size + val_size) > 0 else 0.15
        strat_tv = y_train_val if (config_dict["stratified"] and len(np.unique(y_train_val)) > 1 and np.min(np.bincount(y_train_val)) >= 2) else None

        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val, test_size=val_relative_ratio, stratify=strat_tv, random_state=42
        )

        # 7. Fit Preprocessor strictly on training data
        bundle = PreprocessingBundle.infer_and_create(X_train, feature_cols)
        X_train_trans = bundle.fit_transform(X_train)
        X_val_trans = bundle.transform(X_val)
        X_test_trans = bundle.transform(X_test)

        dataset_meta = {
            "dataset_id": dataset_id,
            "dataset_name": dataset_row["name"],
            "label_mapping": {"normal": norm_val, "anomaly": anom_val}
        }

        trained_results = {}

        # 8. Train Random Forest
        if "random_forest" in algorithms:
            rf_id = f"rf_{uuid.uuid4().hex[:8]}"
            rf_model = RandomForestModelWrapper(model_id=rf_id, hyperparameters=rf_params)
            rf_model.feature_names = bundle.transformed_feature_names

            start_t = time.time()
            rf_model.fit(X_train_trans, y_train)
            duration = round(time.time() - start_t, 3)

            rf_preds = rf_model.predict(X_test_trans)
            rf_probs = rf_model.predict_proba(X_test_trans)
            rf_metrics = EvaluationMetrics.evaluate(y_test, rf_preds, rf_probs)
            rf_metrics["training_duration_seconds"] = duration
            rf_metrics["test_samples"] = len(y_test)
            rf_metrics["train_samples"] = len(y_train)
            rf_metrics["val_samples"] = len(y_val)

            # Validate 3-level classification policy on validation split
            try:
                rf_val_probs = rf_model.predict_proba(X_val_trans)
                rf_val_prob_anom = rf_val_probs[:, 1] if rf_val_probs.shape[1] > 1 else rf_val_probs[:, 0]
                policy = RiskClassificationPolicy()
                rf_metrics["classification_policy"] = policy.validate_on_validation_set(
                    y_val=list(y_val),
                    y_probs=[float(p) for p in rf_val_prob_anom]
                )
            except Exception as e:
                rf_metrics["classification_policy"] = {"validated": False, "error": str(e)}

            saved_rf = ModelRegistry.save_model(
                model_wrapper=rf_model,
                preprocessor=bundle,
                metrics=rf_metrics,
                dataset_meta=dataset_meta,
                version=f"1.0.{int(time.time()) % 1000}"
            )
            trained_results["random_forest"] = {
                "model_id": rf_id,
                "name": rf_model.name,
                "metrics": rf_metrics,
                "artifact": saved_rf
            }

        # 9. Train XGBoost
        if "xgboost" in algorithms:
            xgb_id = f"xgb_{uuid.uuid4().hex[:8]}"
            xgb_model = XGBoostModelWrapper(model_id=xgb_id, hyperparameters=xgb_params)
            xgb_model.feature_names = bundle.transformed_feature_names

            start_t = time.time()
            xgb_model.fit(X_train_trans, y_train, X_val_trans, y_val)
            duration = round(time.time() - start_t, 3)

            xgb_preds = xgb_model.predict(X_test_trans)
            xgb_probs = xgb_model.predict_proba(X_test_trans)
            xgb_metrics = EvaluationMetrics.evaluate(y_test, xgb_preds, xgb_probs)
            xgb_metrics["training_duration_seconds"] = duration
            xgb_metrics["test_samples"] = len(y_test)
            xgb_metrics["train_samples"] = len(y_train)
            xgb_metrics["val_samples"] = len(y_val)

            # Validate 3-level classification policy on validation split
            try:
                xgb_val_probs = xgb_model.predict_proba(X_val_trans)
                xgb_val_prob_anom = xgb_val_probs[:, 1] if xgb_val_probs.shape[1] > 1 else xgb_val_probs[:, 0]
                policy = RiskClassificationPolicy()
                xgb_metrics["classification_policy"] = policy.validate_on_validation_set(
                    y_val=list(y_val),
                    y_probs=[float(p) for p in xgb_val_prob_anom]
                )
            except Exception as e:
                xgb_metrics["classification_policy"] = {"validated": False, "error": str(e)}

            saved_xgb = ModelRegistry.save_model(
                model_wrapper=xgb_model,
                preprocessor=bundle,
                metrics=xgb_metrics,
                dataset_meta=dataset_meta,
                version=f"1.0.{int(time.time()) % 1000}"
            )
            trained_results["xgboost"] = {
                "model_id": xgb_id,
                "name": xgb_model.name,
                "metrics": xgb_metrics,
                "artifact": saved_xgb
            }

        return {
            "success": True,
            "dataset_id": dataset_id,
            "dataset_name": dataset_row["name"],
            "split_summary": {
                "train_samples": len(X_train),
                "val_samples": len(X_val),
                "test_samples": len(X_test),
                "total_valid": len(df_clean)
            },
            "models": trained_results,
            "warnings": warnings
        }
