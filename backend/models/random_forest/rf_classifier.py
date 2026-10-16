from typing import Dict, Any, Optional, List
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from backend.models.base import BaseModelWrapper

class RandomForestModelWrapper(BaseModelWrapper):
    """Wrapper for scikit-learn RandomForestClassifier."""

    def __init__(self, model_id: str, name: str = "Random Forest Classifier", hyperparameters: Dict[str, Any] = None):
        super().__init__(model_id=model_id, name=name, algorithm="random_forest", hyperparameters=hyperparameters)
        
        # Hyperparameters with safe defaults
        self.n_estimators = int(self.hyperparameters.get("n_estimators", 100))
        self.max_depth = int(self.hyperparameters.get("max_depth", 15)) if self.hyperparameters.get("max_depth") else None
        self.min_samples_split = int(self.hyperparameters.get("min_samples_split", 2))
        self.min_samples_leaf = int(self.hyperparameters.get("min_samples_leaf", 1))
        self.class_weight = self.hyperparameters.get("class_weight", "balanced")
        self.random_state = int(self.hyperparameters.get("random_state", 42))

        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            class_weight=self.class_weight,
            random_state=self.random_state,
            n_jobs=-1
        )

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> "RandomForestModelWrapper":
        """Fit Random Forest on X_train, y_train."""
        self.model.fit(X_train, y_train)
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
        # If single class trained (edge case), pad to 2 classes
        if probs.shape[1] == 1:
            classes = self.model.classes_
            if classes[0] == 0:
                probs = np.column_stack([probs[:, 0], np.zeros(len(X))])
            else:
                probs = np.column_stack([np.zeros(len(X)), probs[:, 0]])
        return probs

    def get_feature_importances(self) -> Dict[str, float]:
        """Return Gini feature importances."""
        if not self.is_trained or not hasattr(self.model, "feature_importances_"):
            return {}
        importances = self.model.feature_importances_
        if self.feature_names and len(self.feature_names) == len(importances):
            return {name: round(float(val), 5) for name, val in zip(self.feature_names, importances)}
        return {f"feature_{i}": round(float(val), 5) for i, val in enumerate(importances)}
