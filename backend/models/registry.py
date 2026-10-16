import os
import json
import joblib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from backend.config import Config
from backend.database.db import query_all, query_one, execute_write

class ModelRegistry:
    """Manages model serialization, versioning, metadata storage, and active model status."""

    @classmethod
    def save_model(
        cls,
        model_wrapper,
        preprocessor,
        metrics: Dict[str, Any],
        dataset_meta: Dict[str, Any],
        version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """Serialize model bundle and register in SQLite database."""
        Config.init_directories()

        model_id = model_wrapper.model_id
        artifact_filename = f"{model_id}.joblib"
        artifact_path = os.path.join(Config.ARTIFACT_FOLDER, artifact_filename)

        bundle = {
            "model_id": model_id,
            "name": model_wrapper.name,
            "algorithm": model_wrapper.algorithm,
            "version": version,
            "hyperparameters": model_wrapper.hyperparameters,
            "model": model_wrapper.model,
            "preprocessor": preprocessor,
            "metrics": metrics,
            "feature_schema": preprocessor.to_dict(),
            "dataset_id": dataset_meta.get("dataset_id"),
            "dataset_name": dataset_meta.get("dataset_name"),
            "label_mapping": dataset_meta.get("label_mapping", {"normal": "0", "anomaly": "1"}),
            "saved_at": datetime.utcnow().isoformat()
        }

        # Save binary artifact
        joblib.dump(bundle, artifact_path)

        # Register in DB
        now_str = datetime.utcnow().isoformat()
        execute_write(
            """INSERT OR REPLACE INTO models (
                id, name, algorithm, version, dataset_id, dataset_name,
                hyperparameters_json, metrics_json, feature_schema_json,
                artifact_path, is_active, training_duration_seconds, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                model_id,
                model_wrapper.name,
                model_wrapper.algorithm,
                version,
                dataset_meta.get("dataset_id"),
                dataset_meta.get("dataset_name"),
                json.dumps(model_wrapper.hyperparameters),
                json.dumps(metrics),
                json.dumps(preprocessor.to_dict()),
                artifact_path,
                0,  # Inactive by default until user explicitly activates
                float(metrics.get("training_duration_seconds", 0.0)),
                now_str
            )
        )

        return {
            "id": model_id,
            "model_id": model_id,
            "name": model_wrapper.name,
            "algorithm": model_wrapper.algorithm,
            "version": version,
            "artifact_path": artifact_path,
            "created_at": now_str
        }

    @classmethod
    def load_bundle(cls, model_id: str) -> Optional[Dict[str, Any]]:
        """Load full serialized bundle by model_id."""
        row = query_one("SELECT * FROM models WHERE id = ?", (model_id,))
        if not row:
            return None

        artifact_path = row["artifact_path"]
        if not os.path.exists(artifact_path):
            raise FileNotFoundError(f"Model artifact not found at path: {artifact_path}")

        return joblib.load(artifact_path)

    @classmethod
    
    def get_active_model(cls) -> Optional[Dict[str, Any]]:
        """Retrieve a single active model (legacy). Returns the first active model if multiple are active."""
        row = query_one("SELECT * FROM models WHERE is_active = 1 LIMIT 1")
        if not row:
            return None
        return cls._format_model_row(row)

    @classmethod
    def get_active_models(cls) -> List[Dict[str, Any]]:
        """Retrieve all models marked as active."""
        rows = query_all("SELECT * FROM models WHERE is_active = 1")
        return [cls._format_model_row(r) for r in rows]

    @classmethod
    def activate_models(cls, model_ids: List[str]) -> bool:
        """Activate multiple models without deactivating others.
        Ensures each model exists and its artifact file is present.
        Returns True on success.
        """
        # Validate all models first
        for mid in model_ids:
            row = query_one("SELECT * FROM models WHERE id = ?", (mid,))
            if not row:
                raise ValueError(f"Model with id '{mid}' does not exist.")
            if not os.path.exists(row["artifact_path"]):
                raise FileNotFoundError(f"Model artifact missing at {row['artifact_path']}")
        # Activate models
        placeholders = ",".join(["?" for _ in model_ids])
        # Set specified ids to active
        execute_write(f"UPDATE models SET is_active = 1 WHERE id IN ({placeholders})", tuple(model_ids))
        return True

    @classmethod
    def activate_model(cls, model_id: str) -> bool:
        """Set a validated model as the active inference model."""
        row = query_one("SELECT * FROM models WHERE id = ?", (model_id,))
        if not row:
            raise ValueError(f"Model with id '{model_id}' does not exist.")

        # Ensure artifact file exists on disk
        if not os.path.exists(row["artifact_path"]):
            raise FileNotFoundError(f"Cannot activate model: artifact missing at {row['artifact_path']}")

        # Atomic transaction: set all to 0, then chosen to 1
        execute_write("UPDATE models SET is_active = 0")
        execute_write("UPDATE models SET is_active = 1 WHERE id = ?", (model_id,))
        return True

    @classmethod
    def list_models(cls) -> List[Dict[str, Any]]:
        """List all registered models with their metrics."""
        rows = query_all("SELECT * FROM models ORDER BY created_at DESC")
        return [cls._format_model_row(r) for r in rows]

    @classmethod
    def get_model(cls, model_id: str) -> Optional[Dict[str, Any]]:
        """Get single model metadata."""
        row = query_one("SELECT * FROM models WHERE id = ?", (model_id,))
        return cls._format_model_row(row) if row else None

    @classmethod
    def validate_feature_compatibility(cls, bundle: Dict[str, Any], input_columns: List[str]) -> Tuple[bool, List[str]]:
        """Check if incoming log features match model expected features."""
        expected = bundle["feature_schema"]["feature_columns"]
        missing = [c for c in expected if c not in input_columns]
        is_compatible = len(missing) == 0
        return is_compatible, missing

    @classmethod
    def _format_model_row(cls, row: dict) -> dict:
        """Format SQLite row into JSON-ready dict."""
        return {
            "id": row["id"],
            "name": row["name"],
            "algorithm": row["algorithm"],
            "version": row["version"],
            "dataset_id": row["dataset_id"],
            "dataset_name": row["dataset_name"],
            "hyperparameters": json.loads(row["hyperparameters_json"]) if row.get("hyperparameters_json") else {},
            "metrics": json.loads(row["metrics_json"]) if row.get("metrics_json") else {},
            "feature_schema": json.loads(row["feature_schema_json"]) if row.get("feature_schema_json") else {},
            "is_active": bool(row["is_active"]),
            "training_duration_seconds": row["training_duration_seconds"],
            "created_at": row["created_at"]
        }
