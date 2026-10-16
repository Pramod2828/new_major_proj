import pandas as pd
import numpy as np
from typing import Dict, Any, List

class DatasetInspector:
    """Inspects dataset structure, data types, missing values, and candidate columns."""

    TARGET_COLUMN_KEYWORDS = {"label", "class", "target", "anomaly", "is_anomaly", "status", "attack", "tag", "ground_truth", "severity"}
    TIMESTAMP_KEYWORDS = {"time", "timestamp", "datetime", "date", "created_at", "ts", "epoch"}
    MESSAGE_KEYWORDS = {"message", "msg", "log", "content", "raw", "text", "event", "payload", "description"}

    @classmethod
    def inspect(cls, df: pd.DataFrame, sample_size: int = 10) -> Dict[str, Any]:
        """Generate comprehensive structural inspection of a dataset DataFrame."""
        total_rows = len(df)
        total_cols = len(df.columns)
        duplicate_rows = int(df.duplicated().sum())

        columns_info = []
        candidate_targets = []
        candidate_timestamps = []
        candidate_messages = []

        for col in df.columns:
            col_series = df[col]
            null_count = int(col_series.isnull().sum())
            null_pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
            unique_count = int(col_series.nunique(dropna=True))

            # Infer data type
            dtype_str = str(col_series.dtype)
            is_numeric = pd.api.types.is_numeric_dtype(col_series)
            is_object = pd.api.types.is_object_dtype(col_series) or pd.api.types.is_string_dtype(col_series)
            is_bool = pd.api.types.is_bool_dtype(col_series)

            # Get up to 5 sample non-null values
            sample_vals = col_series.dropna().head(5).tolist()
            sample_vals_clean = [cls._clean_value(v) for v in sample_vals]

            # Unique values if cardinality is small (<= 10)
            unique_values = []
            if unique_count <= 10:
                unique_values = [cls._clean_value(v) for v in col_series.dropna().unique().tolist()]

            col_meta = {
                "name": str(col),
                "dtype": dtype_str,
                "is_numeric": is_numeric,
                "is_categorical": is_object or is_bool,
                "null_count": null_count,
                "null_percent": null_pct,
                "unique_count": unique_count,
                "sample_values": sample_vals_clean,
                "unique_values": unique_values
            }
            columns_info.append(col_meta)

            col_lower = str(col).lower()

            # Target column heuristic
            if (1 < unique_count <= 10) or any(k in col_lower for k in cls.TARGET_COLUMN_KEYWORDS):
                val_counts = col_series.value_counts(dropna=False).head(10).to_dict()
                distribution = {str(k): int(v) for k, v in val_counts.items()}
                candidate_targets.append({
                    "column": str(col),
                    "unique_count": unique_count,
                    "distribution": distribution,
                    "keyword_match": any(k in col_lower for k in cls.TARGET_COLUMN_KEYWORDS)
                })

            # Timestamp heuristic
            if any(k in col_lower for k in cls.TIMESTAMP_KEYWORDS):
                candidate_timestamps.append(str(col))

            # Message heuristic
            if is_object and any(k in col_lower for k in cls.MESSAGE_KEYWORDS):
                candidate_messages.append(str(col))

        # Sample preview records
        preview_df = df.head(sample_size).replace({np.nan: None})
        preview_records = []
        for _, row in preview_df.iterrows():
            clean_row = {str(k): cls._clean_value(v) for k, v in row.items()}
            preview_records.append(clean_row)

        return {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "duplicate_rows": duplicate_rows,
            "columns": columns_info,
            "candidate_targets": candidate_targets,
            "candidate_timestamps": candidate_timestamps,
            "candidate_messages": candidate_messages,
            "preview_records": preview_records
        }

    @staticmethod
    def _clean_value(val):
        """Ensure values are JSON-serializable."""
        if pd.isna(val) or val is None:
            return None
        if isinstance(val, (np.integer, int)):
            return int(val)
        if isinstance(val, (np.floating, float)):
            return float(val) if not np.isnan(val) else None
        if isinstance(val, (np.bool_, bool)):
            return bool(val)
        return str(val)
