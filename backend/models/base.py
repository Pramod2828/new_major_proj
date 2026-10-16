from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd

class BaseModelWrapper(ABC):
    """Abstract base class for supervised anomaly detection models."""

    def __init__(self, model_id: str, name: str, algorithm: str, hyperparameters: Dict[str, Any] = None):
        self.model_id = model_id
        self.name = name
        self.algorithm = algorithm
        self.hyperparameters = hyperparameters or {}
        self.model = None
        self.feature_names = []
        self.is_trained = False

    @abstractmethod
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> "BaseModelWrapper":
        """Fit model on training split with optional validation split."""
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict binary class (0=Normal, 1=Anomaly)."""
        pass

    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict probability scores for classes [Normal, Anomaly]."""
        pass

    @abstractmethod
    def get_feature_importances(self) -> Dict[str, float]:
        """Return native feature importances mapped to feature names."""
        pass
