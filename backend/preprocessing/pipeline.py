import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

class PreprocessingBundle:
    """Manages feature preprocessing, imputation, scaling, encoding, and schema preservation."""

    def __init__(self, feature_columns: List[str], numerical_cols: List[str] = None, categorical_cols: List[str] = None):
        self.feature_columns = list(feature_columns)
        self.numerical_cols = list(numerical_cols) if numerical_cols is not None else []
        self.categorical_cols = list(categorical_cols) if categorical_cols is not None else []
        self.transformer: ColumnTransformer = None
        self.transformed_feature_names: List[str] = []
        self.is_fitted = False

    @classmethod
    def infer_and_create(cls, X: pd.DataFrame, feature_columns: List[str]) -> "PreprocessingBundle":
        """Infer numerical and categorical columns from sample DataFrame and create bundle."""
        X_sub = X[feature_columns]
        numerical = []
        categorical = []
        for col in feature_columns:
            if pd.api.types.is_numeric_dtype(X_sub[col]):
                numerical.append(col)
            else:
                categorical.append(col)
        return cls(feature_columns=feature_columns, numerical_cols=numerical, categorical_cols=categorical)

    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        """Fit preprocessor strictly on training data and return transformed numpy array."""
        # Ensure correct column subset and ordering
        X_in = self._prepare_input(X)

        transformers = []
        if self.numerical_cols:
            num_pipe = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler())
            ])
            transformers.append(("num", num_pipe, self.numerical_cols))

        if self.categorical_cols:
            cat_pipe = Pipeline([
                ("imputer", SimpleImputer(strategy="constant", fill_value="_MISSING_")),
                ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
            ])
            transformers.append(("cat", cat_pipe, self.categorical_cols))

        if not transformers:
            raise ValueError("No features available for preprocessing.")

        self.transformer = ColumnTransformer(transformers=transformers, remainder="drop")
        transformed_arr = self.transformer.fit_transform(X_in)
        self.is_fitted = True

        # Extract output feature names for explainability and inspection
        names = []
        if self.numerical_cols:
            names.extend(self.numerical_cols)
        if self.categorical_cols:
            try:
                cat_encoder = self.transformer.named_transformers_["cat"].named_steps["encoder"]
                cat_names = cat_encoder.get_feature_names_out(self.categorical_cols)
                names.extend(list(cat_names))
            except Exception:
                names.extend([f"cat_{c}" for c in self.categorical_cols])
        self.transformed_feature_names = names

        return np.asarray(transformed_arr, dtype=np.float32)

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform test/validation/inference data using already fitted preprocessor."""
        if not self.is_fitted or self.transformer is None:
            raise RuntimeError("Preprocessor has not been fitted yet.")
        X_in = self._prepare_input(X)
        transformed_arr = self.transformer.transform(X_in)
        return np.asarray(transformed_arr, dtype=np.float32)

    def _prepare_input(self, X: pd.DataFrame) -> pd.DataFrame:
        """Ensure input DataFrame contains all required columns with correct types."""
        missing = [c for c in self.feature_columns if c not in X.columns]
        if missing:
            raise ValueError(f"Input is missing required features: {missing}")

        X_copy = X[self.feature_columns].copy()
        # Convert numeric cols to numeric, coercing invalid
        for col in self.numerical_cols:
            X_copy[col] = pd.to_numeric(X_copy[col], errors="coerce")
        # Convert categorical cols to string
        for col in self.categorical_cols:
            X_copy[col] = X_copy[col].astype(str).replace({"nan": "_MISSING_", "None": "_MISSING_"})

        return X_copy

    def to_dict(self) -> Dict[str, Any]:
        """Metadata representation of feature schema."""
        return {
            "feature_columns": self.feature_columns,
            "numerical_cols": self.numerical_cols,
            "categorical_cols": self.categorical_cols,
            "transformed_feature_names": self.transformed_feature_names,
            "is_fitted": self.is_fitted,
            "num_features_in": len(self.feature_columns),
            "num_features_out": len(self.transformed_feature_names)
        }
