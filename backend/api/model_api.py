from flask import Blueprint, request, jsonify
from backend.models.registry import ModelRegistry
from backend.database.db import query_all, query_one

model_bp = Blueprint("models", __name__)

@model_bp.route("/models", methods=["GET"])
def list_models():
    """List all registered models with their performance metrics."""
    models = ModelRegistry.list_models()
    return jsonify(models), 200

@model_bp.route("/models/active", methods=["GET"])
def get_active_model():
    """Retrieve active model information."""
    model = ModelRegistry.get_active_model()
    if not model:
        return jsonify({
            "active": False,
            "message": "No active model set. Please activate a validated model."
        }), 200
    return jsonify({
        "active": True,
        "model": model
    }), 200

@model_bp.route("/models/<model_id>", methods=["GET"])
def get_model(model_id):
    """Get single model metadata and metrics."""
    model = ModelRegistry.get_model(model_id)
    if not model:
        return jsonify({"error": "Model not found"}), 404
    return jsonify(model), 200

@model_bp.route("/models/activate", methods=["POST"])
def activate_models():
    """Activate multiple models for production inference.
    Expects JSON body: {"model_ids": ["id1", "id2", ...]}
    """
    data = request.get_json()
    if not data or 'model_ids' not in data:
        return jsonify({"error": "Missing 'model_ids' in request body."}), 400
    model_ids = data['model_ids']
    if not isinstance(model_ids, list) or not all(isinstance(mid, str) for mid in model_ids):
        return jsonify({"error": "'model_ids' must be a list of string IDs."}), 400
    try:
        ModelRegistry.activate_models(model_ids)
        return jsonify({
            "success": True,
            "message": f"Models {', '.join(model_ids)} successfully set as active.",
            "active_model_ids": model_ids
        }), 200
    except Exception as e:
        return jsonify({"error": f"Failed to activate models: {str(e)}"}), 400

@model_bp.route("/models/compare", methods=["GET"])
def compare_models():
    """Compare performance across all trained models (or specific model IDs)."""
    model_ids = request.args.get("ids")
    if model_ids:
        ids_list = model_ids.split(",")
        all_models = [ModelRegistry.get_model(mid) for mid in ids_list if ModelRegistry.get_model(mid)]
    else:
        all_models = ModelRegistry.list_models()

    if not all_models:
        return jsonify({
            "comparison": [],
            "message": "No models available for comparison yet. Train models first."
        }), 200

    comparison_rows = []
    for m in all_models:
        metrics = m.get("metrics", {})
        cm = metrics.get("confusion_matrix", {})
        comparison_rows.append({
            "id": m["id"],
            "name": m["name"],
            "algorithm": m["algorithm"],
            "version": m["version"],
            "is_active": m["is_active"],
            "created_at": m["created_at"],
            "accuracy": metrics.get("accuracy"),
            "precision": metrics.get("precision"),
            "recall": metrics.get("recall"),
            "f1_score": metrics.get("f1_score"),
            "roc_auc": metrics.get("roc_auc"),
            "pr_auc": metrics.get("pr_auc"),
            "false_positive_rate": metrics.get("false_positive_rate"),
            "false_negative_rate": metrics.get("false_negative_rate"),
            "confusion_matrix": cm,
            "roc_curve": metrics.get("roc_curve", []),
            "pr_curve": metrics.get("pr_curve", []),
            "training_duration_seconds": m.get("training_duration_seconds")
        })

    return jsonify({
        "count": len(comparison_rows),
        "comparison": comparison_rows
    }), 200
