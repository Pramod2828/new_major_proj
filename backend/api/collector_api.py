import json
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from backend.collectors.windows_event_collector import get_windows_collector
from backend.database.db import query_one, query_all

collector_bp = Blueprint("collector", __name__)

@collector_bp.route("/collector/status", methods=["GET"])
def get_collector_status():
    """Retrieve live collector status, accessible channels, and 24h event statistics."""
    collector = get_windows_collector()
    return jsonify(collector.get_status()), 200

@collector_bp.route("/collector/pause", methods=["POST"])
def pause_collector():
    """Pause live collection."""
    collector = get_windows_collector()
    collector.pause()
    return jsonify(collector.get_status()), 200

@collector_bp.route("/collector/resume", methods=["POST"])
def resume_collector():
    """Resume live collection."""
    collector = get_windows_collector()
    collector.resume()
    return jsonify(collector.get_status()), 200

@collector_bp.route("/collector/poll-now", methods=["POST"])
def poll_collector_now():
    """Trigger an immediate incremental collection pass."""
    collector = get_windows_collector()
    res = collector.poll_now()
    return jsonify({
        "success": True,
        "poll_result": res,
        "status": collector.get_status()
    }), 200

@collector_bp.route("/collector/events", methods=["GET"])
def get_collector_events():
    """Fetch collected Windows events with time-range, category, channel, and text search filters."""
    time_range = request.args.get("time_range", "24h")
    category = request.args.get("category")
    channel = request.args.get("channel")
    search = request.args.get("search", "").strip()
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    now = datetime.utcnow()
    cutoff_dt = None
    if time_range == "1h":
        cutoff_dt = now - timedelta(hours=1)
    elif time_range == "6h":
        cutoff_dt = now - timedelta(hours=6)
    elif time_range == "12h":
        cutoff_dt = now - timedelta(hours=12)
    elif time_range == "24h":
        cutoff_dt = now - timedelta(hours=24)
    elif time_range == "7d":
        cutoff_dt = now - timedelta(days=7)
    # "all" leaves cutoff_dt as None

    where_clauses = ["1=1"]
    params = []

    if cutoff_dt:
        where_clauses.append("timestamp >= ?")
        params.append(cutoff_dt.isoformat())

    if category and category.lower() != "all":
        if category == "Unclassified":
            where_clauses.append("(category = 'Unclassified' OR category IS NULL)")
        else:
            where_clauses.append("category = ?")
            params.append(category)

    if channel and channel.lower() != "all":
        where_clauses.append("channel = ?")
        params.append(channel)

    if search:
        where_clauses.append("(raw_log LIKE ? OR provider LIKE ? OR explanation_summary LIKE ?)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])

    where_str = " AND ".join(where_clauses)

    # Total matching count
    count_sql = f"SELECT COUNT(*) as c FROM predictions WHERE {where_str}"
    total_matching = query_one(count_sql, tuple(params))["c"]

    # Paginated rows
    query_sql = f"""
        SELECT id, batch_id, model_name, model_version, raw_log,
               prediction, probability, is_anomaly, category, risk_score, confidence,
               explanation_summary, observed_facts_json, model_explanation_json, security_interpretation,
               shap_values_json, timestamp, channel, record_id, event_id, provider, severity_label
        FROM predictions
        WHERE {where_str}
        ORDER BY timestamp DESC
        LIMIT ? OFFSET ?
    """
    query_params = list(params) + [limit, offset]
    rows = query_all(query_sql, tuple(query_params))

    events = []
    for r in rows:
        observed_facts = json.loads(r["observed_facts_json"]) if r.get("observed_facts_json") else {}
        model_explanation = json.loads(r["model_explanation_json"]) if r.get("model_explanation_json") else {}
        shap_data = json.loads(r["shap_values_json"]) if r.get("shap_values_json") else None

        events.append({
            "id": r["id"],
            "batch_id": r["batch_id"],
            "timestamp": r["timestamp"],
            "hostname": observed_facts.get("hostname", "localhost"),
            "provider": r["provider"] or observed_facts.get("application_name", "System"),
            "app_name": r["provider"] or observed_facts.get("application_name", "System"),
            "channel": r["channel"] or observed_facts.get("channel", "System"),
            "event_id": r["event_id"] or observed_facts.get("event_id"),
            "record_id": r["record_id"] or observed_facts.get("record_id"),
            "severity_label": r["severity_label"] or observed_facts.get("severity_label", "Information"),
            "raw_log": r["raw_log"],
            "message": r["raw_log"].split(": ", 1)[1] if ": " in r["raw_log"] else r["raw_log"],
            "category": r["category"] or "Unclassified",
            "classification": r["category"] or "Unclassified",
            "is_anomaly": bool(r["is_anomaly"]),
            "prediction": r["prediction"],
            "probability": r["probability"],
            "risk_score": r["risk_score"],
            "confidence": r["confidence"],
            "explanation_summary": r["explanation_summary"],
            "observed_facts": observed_facts,
            "model_explanation": model_explanation,
            "security_interpretation": r["security_interpretation"],
            "shap": shap_data
        })

    return jsonify({
        "success": True,
        "total": total_matching,
        "limit": limit,
        "offset": offset,
        "time_range": time_range,
        "events": events
    }), 200

@collector_bp.route("/collector/events/<event_id>", methods=["GET"])
def get_collector_event_detail(event_id):
    """Retrieve full detail for a single collected event."""
    row = query_one("SELECT * FROM predictions WHERE id = ?", (event_id,))
    if not row:
        return jsonify({"error": "Event not found"}), 404

    observed_facts = json.loads(row["observed_facts_json"]) if row.get("observed_facts_json") else {}
    model_explanation = json.loads(row["model_explanation_json"]) if row.get("model_explanation_json") else {}
    shap_data = json.loads(row["shap_values_json"]) if row.get("shap_values_json") else None

    return jsonify({
        "id": row["id"],
        "batch_id": row["batch_id"],
        "timestamp": row["timestamp"],
        "hostname": observed_facts.get("hostname", "localhost"),
        "provider": row["provider"] or observed_facts.get("application_name", "System"),
        "channel": row["channel"] or observed_facts.get("channel", "System"),
        "event_id": row["event_id"] or observed_facts.get("event_id"),
        "record_id": row["record_id"] or observed_facts.get("record_id"),
        "severity_label": row["severity_label"] or observed_facts.get("severity_label", "Information"),
        "raw_log": row["raw_log"],
        "message": row["raw_log"].split(": ", 1)[1] if ": " in row["raw_log"] else row["raw_log"],
        "category": row["category"] or "Unclassified",
        "classification": row["category"] or "Unclassified",
        "is_anomaly": bool(row["is_anomaly"]),
        "prediction": row["prediction"],
        "probability": row["probability"],
        "risk_score": row["risk_score"],
        "confidence": row["confidence"],
        "explanation_summary": row["explanation_summary"],
        "observed_facts": observed_facts,
        "model_explanation": model_explanation,
        "security_interpretation": row["security_interpretation"],
        "shap": shap_data
    }), 200
