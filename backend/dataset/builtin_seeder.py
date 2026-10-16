"""
Seed built-in AIT-LDS datasets (FOX, Russell-Mitchell, Santos) into the datasets table
from their existing model artifacts. Run once on startup or as a migration.
"""
import os
import sys
import json
import joblib
from datetime import datetime

# Allow running as script or importing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.database.db import execute_write, query_one

# Built-in dataset metadata derived from the trained model artifacts
BUILTIN_DATASETS = [
    {
        "id": "builtin_fox",
        "name": "AIT-LDS FOX",
        "source": "AIT Log Data Set — FOX Scenario (2022-01-15 to 2022-01-20)",
        "description": "Multi-day network intrusion scenario with labeled attack/normal syslog events from the AIT-LDS (Fox) benchmark.",
        "row_count": 186077,      # Total processed records across the scenario
        "col_count": 11,          # Feature columns used for training
        "format": "builtin",
        "status": "approved",
        "dataset_type": "builtin",
        "target_column": "label",
        "normal_label": "0",
        "anomaly_label": "1",
        "feature_columns": ["message_length", "token_count", "digit_ratio", "entropy",
                             "has_error", "has_warning", "has_auth", "has_failed_auth",
                             "has_denied", "has_ip", "service"],
        "model_ids": ["ait_fox_random_forest_20261015_042726", "ait_fox_xgboost_20261015_042847"],
        "train_split": 0.80,
        "val_split": 0.20,
        "train_rows": 148861,
        "val_rows": 37216,
        "duplicate_rows": 0,
    },
    {
        "id": "builtin_russellmitchell",
        "name": "AIT-LDS Russell-Mitchell",
        "source": "AIT Log Data Set — Russell-Mitchell Scenario",
        "description": "Labeled syslog dataset covering authentication attacks and privilege escalation in the Russell-Mitchell scenario.",
        "row_count": 63603,
        "col_count": 11,
        "format": "builtin",
        "status": "approved",
        "dataset_type": "builtin",
        "target_column": "label",
        "normal_label": "0",
        "anomaly_label": "1",
        "feature_columns": ["message_length", "token_count", "digit_ratio", "entropy",
                             "has_error", "has_warning", "has_auth", "has_failed_auth",
                             "has_denied", "has_ip", "service"],
        "model_ids": ["ait_russellmitchell_random_forest_20261015_042932", "ait_russellmitchell_xgboost_20261015_043019"],
        "train_split": 0.80,
        "val_split": 0.20,
        "train_rows": 50882,
        "val_rows": 12721,
        "duplicate_rows": 0,
    },
    {
        "id": "builtin_santos",
        "name": "AIT-LDS Santos",
        "source": "AIT Log Data Set — Santos Scenario",
        "description": "Labeled syslog dataset with web application attack patterns in the Santos scenario.",
        "row_count": 63629,
        "col_count": 11,
        "format": "builtin",
        "status": "approved",
        "dataset_type": "builtin",
        "target_column": "label",
        "normal_label": "0",
        "anomaly_label": "1",
        "feature_columns": ["message_length", "token_count", "digit_ratio", "entropy",
                             "has_error", "has_warning", "has_auth", "has_failed_auth",
                             "has_denied", "has_ip", "service"],
        "model_ids": ["ait_santos_random_forest_20261015_043045", "ait_santos_xgboost_20261015_043148"],
        "train_split": 0.80,
        "val_split": 0.20,
        "train_rows": 50903,
        "val_rows": 12726,
        "duplicate_rows": 0,
    },
]


def seed_builtin_datasets():
    """Insert built-in datasets if not already present. Safe to run multiple times (idempotent)."""
    seeded = 0
    for ds in BUILTIN_DATASETS:
        existing = query_one("SELECT id FROM datasets WHERE id = ?", (ds["id"],))
        if existing:
            continue  # Already seeded

        columns_json = json.dumps([
            {"name": col, "dtype": "int64" if col.startswith("has_") else ("float64" if col in ("digit_ratio", "entropy") else "int64"),
             "is_numeric": True, "is_categorical": col == "service",
             "null_count": 0, "null_percent": 0.0,
             "unique_count": 2 if col.startswith("has_") else 100,
             "sample_values": [], "unique_values": []}
            for col in ds["feature_columns"]
        ])

        extra_meta = json.dumps({
            "dataset_type": ds["dataset_type"],
            "source": ds["source"],
            "description": ds["description"],
            "target_column": ds["target_column"],
            "normal_label": ds["normal_label"],
            "anomaly_label": ds["anomaly_label"],
            "model_ids": ds["model_ids"],
            "train_split": ds["train_split"],
            "val_split": ds["val_split"],
            "train_rows": ds["train_rows"],
            "val_rows": ds["val_rows"],
            "duplicate_rows": ds["duplicate_rows"],
        })

        now_str = datetime.utcnow().isoformat()
        execute_write(
            """INSERT OR IGNORE INTO datasets
               (id, name, filename, file_path, format, row_count, col_count,
                columns_json, sample_json, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                ds["id"],
                ds["name"],
                ds["source"],
                "",            # No local file path for built-ins
                ds["format"],
                ds["row_count"],
                ds["col_count"],
                columns_json,
                extra_meta,   # Repurpose sample_json to store extra metadata for built-ins
                ds["status"],
                now_str
            )
        )

        # Also insert a dataset_config so the dataset is immediately configured
        cfg_id = f"cfg_builtin_{ds['id']}"
        execute_write(
            """INSERT OR IGNORE INTO dataset_configs
               (id, dataset_id, target_column, normal_value, anomaly_value,
                feature_columns_json, timestamp_column, message_column,
                train_ratio, val_ratio, test_ratio, stratified, is_approved,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                cfg_id,
                ds["id"],
                ds["target_column"],
                ds["normal_label"],
                ds["anomaly_label"],
                json.dumps(ds["feature_columns"]),
                None,
                None,
                ds["train_split"],
                ds["val_split"],
                1.0 - ds["train_split"] - ds["val_split"],
                1,  # stratified
                1,  # approved
                now_str,
                now_str
            )
        )
        seeded += 1

    return seeded


if __name__ == "__main__":
    n = seed_builtin_datasets()
    print(f"Seeded {n} built-in datasets.")
