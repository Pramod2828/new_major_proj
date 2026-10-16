import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

class DatasetValidator:
    """Validates dataset configuration, target label mapping, and leakage prevention."""

    @classmethod
    def validate_configuration(
        cls,
        df: pd.DataFrame,
        config: Dict[str, Any]
    ) -> Tuple[bool, List[str], List[str]]:
        """Validate dataset against configuration settings.
        
        Args:
            df: Dataset DataFrame
            config: Configuration dictionary with target_column, normal_value, anomaly_value,
                    feature_columns, train_ratio, val_ratio, test_ratio.
                    
        Returns:
            Tuple of (is_valid, errors_list, warnings_list)
        """
        errors = []
        warnings = []

        target_col = config.get("target_column")
        normal_val = config.get("normal_value")
        anomaly_val = config.get("anomaly_value")
        feature_cols = config.get("feature_columns", [])
        train_ratio = float(config.get("train_ratio", 0.70))
        val_ratio = float(config.get("val_ratio", 0.15))
        test_ratio = float(config.get("test_ratio", 0.15))

        # 1. Target column check
        if not target_col:
            errors.append("Target label column must be specified.")
            return False, errors, warnings

        if target_col not in df.columns:
            errors.append(f"Target column '{target_col}' does not exist in dataset.")
            return False, errors, warnings

        # 2. Target mapping check
        if normal_val is None or anomaly_val is None:
            errors.append("Both Normal and Anomaly label values must be specified.")
            return False, errors, warnings

        if str(normal_val) == str(anomaly_val):
            errors.append("Normal label value and Anomaly label value cannot be identical.")

        # Check values present in column
        raw_vals = set(str(v) for v in df[target_col].dropna().unique())
        if str(normal_val) not in raw_vals:
            errors.append(f"Normal value '{normal_val}' was not found in column '{target_col}'. Available values: {sorted(list(raw_vals))}")
        if str(anomaly_val) not in raw_vals:
            errors.append(f"Anomaly value '{anomaly_val}' was not found in column '{target_col}'. Available values: {sorted(list(raw_vals))}")

        # Check for unmapped values in target column
        unmapped = raw_vals - {str(normal_val), str(anomaly_val)}
        if unmapped:
            warnings.append(f"Target column contains values not mapped to Normal or Anomaly: {sorted(list(unmapped))}. These will be dropped or treated as unmapped.")

        null_target_count = df[target_col].isnull().sum()
        if null_target_count > 0:
            warnings.append(f"Target column contains {null_target_count} missing (NaN) values. Rows with missing targets will be dropped during training.")

        # 3. Feature columns check
        if not feature_cols or not isinstance(feature_cols, list):
            errors.append("At least one feature column must be selected.")
        else:
            missing_cols = [c for c in feature_cols if c not in df.columns]
            if missing_cols:
                errors.append(f"Feature columns not found in dataset: {missing_cols}")

            # 4. Target Leakage check
            if target_col in feature_cols:
                errors.append(f"CRITICAL LEAKAGE: Target column '{target_col}' cannot be included in feature columns.")

        # 5. Check constant or zero-variance features
        for fc in feature_cols:
            if fc in df.columns:
                if df[fc].nunique(dropna=True) <= 1:
                    warnings.append(f"Feature '{fc}' has constant or zero variance (only 1 unique value).")

        # 6. Split ratio checks
        total_ratio = round(train_ratio + val_ratio + test_ratio, 4)
        if abs(total_ratio - 1.0) > 0.01:
            errors.append(f"Split ratios must sum to 1.0 (currently sums to {total_ratio}).")
        if train_ratio < 0.50:
            warnings.append(f"Train split ratio ({train_ratio}) is unusually low (< 0.50).")
        if test_ratio <= 0.05:
            warnings.append(f"Test split ratio ({test_ratio}) is very small (<= 0.05).")

        # 7. Minimum sample counts
        mapped_df = df[df[target_col].astype(str).isin([str(normal_val), str(anomaly_val)])]
        total_valid = len(mapped_df)
        if total_valid < 20:
            errors.append(f"Dataset has only {total_valid} valid labelled records; at least 20 are required for train/val/test splits.")
        else:
            anomaly_count = (mapped_df[target_col].astype(str) == str(anomaly_val)).sum()
            normal_count = (mapped_df[target_col].astype(str) == str(normal_val)).sum()
            if anomaly_count < 2:
                errors.append(f"Anomaly class has only {anomaly_count} instances; at least 2 are required for stratified splitting.")
            if normal_count < 2:
                errors.append(f"Normal class has only {normal_count} instances; at least 2 are required for stratified splitting.")

        is_valid = len(errors) == 0
        return is_valid, errors, warnings
