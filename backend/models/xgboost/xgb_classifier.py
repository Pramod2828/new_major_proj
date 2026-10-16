from typing import Dict, Any, Optional, List
import numpy as np
import xgboost as xgb
from backend.models.base import BaseModelWrapper

class XGBoostModelWrapper(BaseModelWrapper):
    """Wrapper for XGBClassifier."""

    def __init__(self, model_id: str, name: str = "XGBoost Classifier", hyperparameters: Dict[str, Any] = None):
        super().__init__(model_id=model_id, name=name, algorithm="xgboost", hyperparameters=hyperparameters)

        # Configurable hyperparameters
        self.n_estimators = int(self.hyperparameters.get("n_estimators", 100))
        self.max_depth = int(self.hyperparameters.get("max_depth", 6))
        self.learning_rate = float(self.hyperparameters.get("learning_rate", 0.1))
        self.subsample = float(self.hyperparameters.get("subsample", 0.8))
        self.colsample_bytree = float(self.hyperparameters.get("colsample_bytree", 0.8))
        self.scale_pos_weight = float(self.hyperparameters.get("scale_pos_weight", 1.0))
        self.random_state = int(self.hyperparameters.get("random_state", 42))
        self.early_stopping_rounds = self.hyperparameters.get("early_stopping_rounds")
        if self.early_stopping_rounds is not None:
            self.early_stopping_rounds = int(self.early_stopping_rounds)

        params = {
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "learning_rate": self.learning_rate,
            "subsample": self.subsample,
            "colsample_bytree": self.colsample_bytree,
            "scale_pos_weight": self.scale_pos_weight,
            "random_state": self.random_state,
            "eval_metric": "logloss",
            "objective": "binary:logistic",
            "n_jobs": -1
        }
        if self.early_stopping_rounds:
            params["early_stopping_rounds"] = self.early_stopping_rounds

        self.model = xgb.XGBClassifier(**params)

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> "XGBoostModelWrapper":
        """Fit XGBoost model with optional validation evaluation."""
        if X_val is not None and y_val is not None and self.early_stopping_rounds:
            self.model.fit(
                X_train,
                y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
        else:
            self.model.fit(X_train, y_train, verbose=False)

        self.is_trained = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict binary class labels."""
        if not self.is_trained:
            raise RuntimeError("Model has not been trained yet.")
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities."""
        if not self.is_trained:
            raise RuntimeError("Model has not been trained yet.")
        probs = self.model.predict_proba(X)
        if probs.shape[1] == 1:
            probs = np.column_stack([1 - probs[:, 0], probs[:, 0]])
        return probs

    def get_feature_importances(self) -> Dict[str, float]:
        """Return gain/weight feature importances."""
        if not self.is_trained or not hasattr(self.model, "feature_importances_"):
            return {}
        importances = self.model.feature_importances_
        if self.feature_names and len(self.feature_names) == len(importances):
            return {name: round(float(val), 5) for name, val in zip(self.feature_names, importances)}
        return {f"feature_{i}": round(float(val), 5) for i, val in enumerate(importances)}
