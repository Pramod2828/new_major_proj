import os
import uuid
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from backend.config import Config
from backend.dataset.loader import DatasetLoader
from backend.dataset.inspector import DatasetInspector
from backend.dataset.validator import DatasetValidator
from backend.database.db import get_db, query_one, query_all, execute_write

dataset_bp = Blueprint("datasets", __name__)

# ─────────────────────────────────────────────────────────────────────────────
# Helper: determine if a dataset is a built-in (non-deletable) training dataset
# ─────────────────────────────────────────────────────────────────────────────
def _is_builtin(dataset_row: dict) -> bool:
    return dataset_row.get("format") == "builtin" or str(dataset_row.get("id", "")).startswith("builtin_")


def _parse_extra_meta(row: dict) -> dict:
    """For built-in datasets, the sample_json column stores extra metadata."""
    if not _is_builtin(row):
        return {}
    try:
        return json.loads(row.get("sample_json") or "{}")
    except Exception:
        return {}


@dataset_bp.route("/datasets/upload", methods=["POST"])
def upload_dataset():
    """Upload dataset file (CSV, JSON, JSONL)."""
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in Config.ALLOWED_DATASET_EXTENSIONS:
        return jsonify({
            "error": f"Unsupported format '{ext}'. Allowed: {', '.join(Config.ALLOWED_DATASET_EXTENSIONS)}"
        }), 400

    # Ensure secure directory and filename
    Config.init_directories()
    dataset_id = f"ds_{uuid.uuid4().hex[:8]}"
    safe_name = secure_filename(file.filename)

    # Duplicate-filename guard: reject if same filename already exists in uploads
    existing_by_name = query_one("SELECT id FROM datasets WHERE filename = ? AND format != 'builtin'", (safe_name,))
    if existing_by_name:
        return jsonify({"error": f"A dataset named '{safe_name}' already exists. Delete it first or rename your file."}), 409

    dest_path = os.path.join(Config.UPLOAD_FOLDER, f"{dataset_id}_{safe_name}")
    file.save(dest_path)

    try:
        # Load and inspect dataset
        df, meta = DatasetLoader.load(dest_path, max_rows=1000)
        inspection = DatasetInspector.inspect(df, sample_size=10)

        now_str = datetime.utcnow().isoformat()
        execute_write(
            """INSERT INTO datasets (
                id, name, filename, file_path, format, row_count, col_count,
                columns_json, sample_json, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                dataset_id,
                safe_name,
                safe_name,
                dest_path,
                meta["format"],
                meta["loaded_rows"],
                meta["loaded_columns"],
                json.dumps(inspection["columns"]),
                json.dumps(inspection["preview_records"]),
                "unconfigured",
                now_str
            )
        )

        return jsonify({
            "success": True,
            "dataset_id": dataset_id,
            "filename": safe_name,
            "rows": meta["loaded_rows"],
            "columns": meta["loaded_columns"],
            "format": meta["format"],
            "inspection": inspection
        }), 201

    except Exception as e:
        # Cleanup uploaded file if parsing fails
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return jsonify({"error": f"Failed to ingest dataset: {str(e)}"}), 400


@dataset_bp.route("/datasets", methods=["GET"])
def list_datasets():
    """List all registered datasets (built-in + user uploaded)."""
    rows = query_all("SELECT * FROM datasets ORDER BY created_at DESC")
    results = []
    for r in rows:
        cfg = query_one("SELECT * FROM dataset_configs WHERE dataset_id = ?", (r["id"],))
        extra = _parse_extra_meta(r)
        is_builtin = _is_builtin(r)

        # Recover columns list
        columns_list = []
        try:
            raw_cols = json.loads(r.get("columns_json") or "[]")
            if isinstance(raw_cols, list):
                columns_list = [c["name"] if isinstance(c, dict) else str(c) for c in raw_cols]
        except Exception:
            pass

        results.append({
            "id": r["id"],
            "name": r["name"],
            "filename": r["filename"],
            "format": r["format"],
            "row_count": r["row_count"] or 0,
            "col_count": r["col_count"] or 0,
            "status": r["status"],
            "created_at": r["created_at"],
            "is_configured": cfg is not None,
            "is_approved": bool(cfg["is_approved"]) if cfg else is_builtin,
            "is_builtin": is_builtin,
            "dataset_type": extra.get("dataset_type", "uploaded"),
            "source": extra.get("source", r["filename"]),
            "description": extra.get("description", ""),
            "target_column": extra.get("target_column") or (cfg["target_column"] if cfg else None),
            "columns": columns_list,
            "model_ids": extra.get("model_ids", []),
            "train_rows": extra.get("train_rows"),
            "val_rows": extra.get("val_rows"),
            "duplicate_rows": extra.get("duplicate_rows"),
        })
    return jsonify(results), 200


@dataset_bp.route("/datasets/<dataset_id>", methods=["GET"])
def get_dataset(dataset_id):
    """Get single dataset metadata."""
    row = query_one("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
    if not row:
        return jsonify({"error": "Dataset not found"}), 404

    cfg = query_one("SELECT * FROM dataset_configs WHERE dataset_id = ?", (dataset_id,))
    extra = _parse_extra_meta(row)
    is_builtin = _is_builtin(row)

    # Decode columns
    columns_decoded = []
    try:
        raw = json.loads(row.get("columns_json") or "[]")
        if isinstance(raw, list) and len(raw) > 0:
            if isinstance(raw[0], dict):
                columns_decoded = raw
            else:
                columns_decoded = [{"name": str(c), "dtype": "unknown"} for c in raw]
    except Exception:
        pass

    # Decode sample
    sample_decoded = []
    if not is_builtin:
        try:
            sample_decoded = json.loads(row.get("sample_json") or "[]")
        except Exception:
            pass

    return jsonify({
        "id": row["id"],
        "name": row["name"],
        "filename": row["filename"],
        "format": row["format"],
        "row_count": row["row_count"] or 0,
        "col_count": row["col_count"] or 0,
        "columns": columns_decoded,
        "sample": sample_decoded,
        "status": row["status"],
        "created_at": row["created_at"],
        "is_builtin": is_builtin,
        "dataset_type": extra.get("dataset_type", "uploaded"),
        "source": extra.get("source", row["filename"]),
        "description": extra.get("description", ""),
        "model_ids": extra.get("model_ids", []),
        "train_rows": extra.get("train_rows"),
        "val_rows": extra.get("val_rows"),
        "duplicate_rows": extra.get("duplicate_rows"),
        "config": {
            "target_column": cfg["target_column"],
            "normal_value": cfg["normal_value"],
            "anomaly_value": cfg["anomaly_value"],
            "feature_columns": json.loads(cfg["feature_columns_json"]) if cfg.get("feature_columns_json") else [],
            "timestamp_column": cfg["timestamp_column"],
            "message_column": cfg["message_column"],
            "train_ratio": cfg["train_ratio"],
            "val_ratio": cfg["val_ratio"],
            "test_ratio": cfg["test_ratio"],
            "stratified": bool(cfg["stratified"]),
            "is_approved": bool(cfg["is_approved"])
        } if cfg else None
    }), 200


@dataset_bp.route("/datasets/<dataset_id>", methods=["DELETE"])
def delete_dataset(dataset_id):
    """Delete a user-uploaded dataset. Built-in datasets cannot be deleted."""
    row = query_one("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
    if not row:
        return jsonify({"error": "Dataset not found"}), 404

    if _is_builtin(row):
        return jsonify({"error": "Built-in training datasets cannot be deleted."}), 403

    # Remove the uploaded file
    file_path = row.get("file_path", "")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass

    execute_write("DELETE FROM dataset_configs WHERE dataset_id = ?", (dataset_id,))
    execute_write("DELETE FROM datasets WHERE id = ?", (dataset_id,))

    return jsonify({"success": True, "message": "Dataset deleted."}), 200


@dataset_bp.route("/datasets/<dataset_id>/inspect", methods=["GET"])
def inspect_dataset(dataset_id):
    """Perform detailed inspection of dataset structure and distributions."""
    row = query_one("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
    if not row:
        return jsonify({"error": "Dataset not found"}), 404

    is_builtin = _is_builtin(row)
    extra = _parse_extra_meta(row)
    cfg = query_one("SELECT * FROM dataset_configs WHERE dataset_id = ?", (dataset_id,))

    if is_builtin:
        # For built-ins, synthesise an inspection from stored metadata
        feature_cols = []
        if cfg:
            try:
                feature_cols = json.loads(cfg.get("feature_columns_json") or "[]")
            except Exception:
                pass

        DTYPE_MAP = {
            "message_length": "int64", "token_count": "int64",
            "digit_ratio": "float64", "entropy": "float64",
            "has_error": "int64", "has_warning": "int64",
            "has_auth": "int64", "has_failed_auth": "int64",
            "has_denied": "int64", "has_ip": "int64",
            "service": "object"
        }
        columns_info = [
            {
                "name": col,
                "dtype": DTYPE_MAP.get(col, "float64"),
                "is_numeric": col != "service",
                "is_categorical": col == "service",
                "null_count": 0,
                "null_percent": 0.0,
                "unique_count": 2 if col.startswith("has_") else (100 if col == "service" else 0),
                "sample_values": [],
                "unique_values": [0, 1] if col.startswith("has_") else []
            }
            for col in feature_cols
        ]

        target_col = extra.get("target_column", "label")
        normal_lbl = extra.get("normal_label", "0")
        anomaly_lbl = extra.get("anomaly_label", "1")
        train_rows = extra.get("train_rows", 0)
        val_rows = extra.get("val_rows", 0)
        total_rows = row["row_count"] or 0

        inspection = {
            "total_rows": total_rows,
            "total_columns": row["col_count"] or len(feature_cols),
            "duplicate_rows": extra.get("duplicate_rows", 0),
            "columns": columns_info,
            "candidate_targets": [
                {
                    "column": target_col,
                    "unique_count": 2,
                    "distribution": {normal_lbl: train_rows, anomaly_lbl: val_rows},
                    "keyword_match": True
                }
            ],
            "candidate_timestamps": [],
            "candidate_messages": [],
            "preview_records": [],
            "builtin_info": {
                "source": extra.get("source", ""),
                "description": extra.get("description", ""),
                "train_rows": train_rows,
                "val_rows": val_rows,
                "model_ids": extra.get("model_ids", []),
                "feature_columns": feature_cols,
            }
        }
        return jsonify({
            "dataset_id": dataset_id,
            "metadata": {
                "file_path": "",
                "filename": row["name"],
                "format": "builtin",
                "file_size_bytes": 0,
                "loaded_rows": total_rows,
                "loaded_columns": len(feature_cols),
                "column_names": feature_cols
            },
            "inspection": inspection
        }), 200

    # For user-uploaded datasets: load actual file
    try:
        df, meta = DatasetLoader.load(row["file_path"], max_rows=5000)
        inspection = DatasetInspector.inspect(df, sample_size=15)
        return jsonify({
            "dataset_id": dataset_id,
            "metadata": meta,
            "inspection": inspection
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to inspect dataset: {str(e)}"}), 500


@dataset_bp.route("/datasets/<dataset_id>/configure", methods=["POST"])
def configure_dataset(dataset_id):
    """Save target label and feature mappings for dataset."""
    row = query_one("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
    if not row:
        return jsonify({"error": "Dataset not found"}), 404

    if _is_builtin(row):
        return jsonify({"error": "Built-in datasets are pre-configured and cannot be modified."}), 403

    data = request.get_json() or {}
    target_col = data.get("target_column")
    normal_val = data.get("normal_value")
    anomaly_val = data.get("anomaly_value")
    feature_cols = data.get("feature_columns", [])

    if not target_col or normal_val is None or anomaly_val is None:
        return jsonify({"error": "target_column, normal_value, and anomaly_value are required"}), 400

    if not feature_cols:
        return jsonify({"error": "At least one feature column must be selected"}), 400

    now_str = datetime.utcnow().isoformat()
    config_id = f"cfg_{uuid.uuid4().hex[:8]}"

    # Delete existing config if present
    execute_write("DELETE FROM dataset_configs WHERE dataset_id = ?", (dataset_id,))

    execute_write(
        """INSERT INTO dataset_configs (
            id, dataset_id, target_column, normal_value, anomaly_value,
            feature_columns_json, timestamp_column, message_column,
            train_ratio, val_ratio, test_ratio, stratified, is_approved,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            config_id,
            dataset_id,
            str(target_col),
            str(normal_val),
            str(anomaly_val),
            json.dumps(feature_cols),
            data.get("timestamp_column"),
            data.get("message_column"),
            float(data.get("train_ratio", 0.70)),
            float(data.get("val_ratio", 0.15)),
            float(data.get("test_ratio", 0.15)),
            1 if data.get("stratified", True) else 0,
            0,  # Unapproved by default until validation passed
            now_str,
            now_str
        )
    )

    execute_write("UPDATE datasets SET status = 'configured' WHERE id = ?", (dataset_id,))

    return jsonify({"success": True, "config_id": config_id, "status": "configured"}), 200


@dataset_bp.route("/datasets/<dataset_id>/validate", methods=["POST"])
def validate_dataset(dataset_id):
    """Validate dataset against configured mappings to verify training readiness."""
    row = query_one("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
    if not row:
        return jsonify({"error": "Dataset not found"}), 404

    if _is_builtin(row):
        return jsonify({"is_valid": True, "errors": [], "warnings": [], "status": "approved"}), 200

    cfg = query_one("SELECT * FROM dataset_configs WHERE dataset_id = ?", (dataset_id,))
    if not cfg:
        return jsonify({"error": "Dataset has not been configured yet"}), 400

    try:
        df, _ = DatasetLoader.load(row["file_path"])
        config_dict = {
            "target_column": cfg["target_column"],
            "normal_value": cfg["normal_value"],
            "anomaly_value": cfg["anomaly_value"],
            "feature_columns": json.loads(cfg["feature_columns_json"]),
            "train_ratio": cfg["train_ratio"],
            "val_ratio": cfg["val_ratio"],
            "test_ratio": cfg["test_ratio"],
            "stratified": bool(cfg["stratified"])
        }

        is_valid, errors, warnings = DatasetValidator.validate_configuration(df, config_dict)

        new_status = "validated" if is_valid else "invalid"
        execute_write("UPDATE datasets SET status = ? WHERE id = ?", (new_status, dataset_id))

        return jsonify({
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "status": new_status
        }), 200
    except Exception as e:
        return jsonify({"error": f"Validation failed: {str(e)}"}), 500


@dataset_bp.route("/datasets/<dataset_id>/approve", methods=["POST"])
def approve_dataset(dataset_id):
    """Explicitly mark a validated dataset configuration as approved for training."""
    row = query_one("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
    if not row:
        return jsonify({"error": "Dataset not found"}), 404

    if _is_builtin(row):
        return jsonify({"success": True, "message": "Built-in dataset is already approved.", "status": "approved"}), 200

    cfg = query_one("SELECT * FROM dataset_configs WHERE dataset_id = ?", (dataset_id,))
    if not cfg:
        return jsonify({"error": "Dataset must be configured before approval"}), 400

    execute_write("UPDATE dataset_configs SET is_approved = 1 WHERE dataset_id = ?", (dataset_id,))
    execute_write("UPDATE datasets SET status = 'approved' WHERE id = ?", (dataset_id,))

    return jsonify({"success": True, "message": "Dataset approved for training.", "status": "approved"}), 200
