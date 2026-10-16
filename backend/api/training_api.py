import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify

from backend.services.training_service import TrainingService
from backend.database.db import query_one, query_all, execute_write

training_bp = Blueprint("training", __name__)

@training_bp.route("/training/guard", methods=["GET"])
def training_guard():
    """Verify if training is permitted (dataset approved and validated)."""
    approved_datasets = query_all(
        """
        SELECT d.id, d.name, d.status, c.is_approved, d.format, d.file_path
        FROM datasets d
        LEFT JOIN dataset_configs c ON d.id = c.dataset_id
        WHERE d.file_path IS NOT NULL AND d.file_path <> ''
          AND c.is_approved = 1
          AND d.status IN ('validated', 'approved')
        """
    )

    can_train = len(approved_datasets) > 0
    return jsonify({
        "can_train": can_train,
        "approved_datasets": approved_datasets,
        "message": "Training is permitted on approved datasets." if can_train else "Training is currently disabled. You must upload, configure, validate, and approve a dataset before initiating training."
    }), 200

@training_bp.route("/training/train", methods=["POST"])
def start_training():
    """Trigger training pipeline for Random Forest and/or XGBoost on approved dataset."""
    data = request.get_json() or {}
    dataset_id = data.get("dataset_id")
    if not dataset_id:
        return jsonify({"error": "dataset_id is required"}), 400

    # Ensure dataset is approved
    cfg = query_one("SELECT is_approved FROM dataset_configs WHERE dataset_id = ?", (dataset_id,))
    if not cfg or not cfg["is_approved"]:
        return jsonify({
            "error": "Dataset is not approved for training. Validate and approve the dataset configuration first."
        }), 400

    algorithms = data.get("algorithms", ["random_forest", "xgboost"])
    rf_params = data.get("rf_params", {})
    xgb_params = data.get("xgb_params", {})
    split_config = data.get("split_config", {})

    job_id = f"job_{uuid.uuid4().hex[:8]}"
    now_str = datetime.utcnow().isoformat()
    execute_write(
        """INSERT INTO training_jobs (
            id, dataset_id, algorithm, status, progress, message, started_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (job_id, dataset_id, ",".join(algorithms), "running", 10, "Starting model training...", now_str)
    )

    try:
        results = TrainingService.train_models(
            dataset_id=dataset_id,
            algorithms=algorithms,
            rf_params=rf_params,
            xgb_params=xgb_params,
            split_config=split_config
        )

        execute_write(
            """UPDATE training_jobs
               SET status = 'completed', progress = 100, message = 'Training completed successfully.', completed_at = ?
               WHERE id = ?""",
            (datetime.utcnow().isoformat(), job_id)
        )

        return jsonify({
            "success": True,
            "job_id": job_id,
            "training_results": results
        }), 200

    except Exception as e:
        execute_write(
            """UPDATE training_jobs
               SET status = 'failed', error_message = ?, completed_at = ?
               WHERE id = ?""",
            (str(e), datetime.utcnow().isoformat(), job_id)
        )
        return jsonify({"error": f"Training failed: {str(e)}"}), 500
