import os
try:
    import psutil
except ImportError:
    psutil = None
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from backend.config import Config
from backend.database.db import query_one, query_all

system_bp = Blueprint("system", __name__)

@system_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Smart-Log Backend API",
        "version": "1.0.0",
        "database": os.path.exists(Config.DATABASE_PATH)
    }), 200

@system_bp.route("/system/status", methods=["GET"])
def system_status():
    """System resource status and database counts."""
    # Active model
    active_model = query_one("SELECT id, name, algorithm, version FROM models WHERE is_active = 1")
    
    # Counts
    datasets_count = query_one("SELECT COUNT(*) as c FROM datasets")["c"]
    models_count = query_one("SELECT COUNT(*) as c FROM models")["c"]
    predictions_count = query_one("SELECT COUNT(*) as c FROM predictions")["c"]
    normal_count = query_one("SELECT COUNT(*) as c FROM predictions WHERE category = 'Normal'")["c"]
    medium_count = query_one("SELECT COUNT(*) as c FROM predictions WHERE category = 'Medium'")["c"]
    anomalies_count = query_one("SELECT COUNT(*) as c FROM predictions WHERE category = 'Anomalous'")["c"]
    unclassified_count = query_one("SELECT COUNT(*) as c FROM predictions WHERE category = 'Unclassified' OR category IS NULL")["c"]

    # System metrics with fallback
    cpu_percent = psutil.cpu_percent(interval=None) if psutil else 0.0
    mem_percent = psutil.virtual_memory().percent if psutil else 0.0
    mem_avail = round(psutil.virtual_memory().available / (1024 * 1024), 2) if psutil else 0.0

    return jsonify({
        "active_model": active_model,
        "counts": {
            "datasets": datasets_count,
            "models": models_count,
            "total_predictions": predictions_count,
            "normal_events": normal_count,
            "medium_events": medium_count,
            "anomalies_flagged": anomalies_count,
            "unclassified_events": unclassified_count
        },
        "system_resources": {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": mem_percent,
            "memory_available_mb": mem_avail
        },
        "storage": {
            "database_exists": os.path.exists(Config.DATABASE_PATH),
            "upload_folder": Config.UPLOAD_FOLDER,
            "artifact_folder": Config.ARTIFACT_FOLDER
        }
    }), 200

@system_bp.route("/dashboard/stats", methods=["GET"])
def dashboard_stats():
    """Overview statistics for dashboard widgets with configurable time range and 24-hour timeline."""
    time_range = request.args.get("time_range", "24h")
    now = datetime.utcnow()

    # Time filtering
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
    elif time_range == "30d":
        cutoff_dt = now - timedelta(days=30)
    # "all" leaves cutoff_dt as None

    where_clause = ""
    params = []
    if cutoff_dt:
        where_clause = " WHERE timestamp >= ?"
        params.append(cutoff_dt.isoformat())

    # Calculate actual stored event counts
    total_logs = query_one(f"SELECT COUNT(*) as c FROM predictions{where_clause}", tuple(params))["c"]
    
    where_normal = (where_clause + " AND " if where_clause else " WHERE ") + "category = 'Normal'"
    normal_count = query_one(f"SELECT COUNT(*) as c FROM predictions{where_normal}", tuple(params))["c"]

    where_medium = (where_clause + " AND " if where_clause else " WHERE ") + "category = 'Medium'"
    medium_count = query_one(f"SELECT COUNT(*) as c FROM predictions{where_medium}", tuple(params))["c"]

    where_anomalous = (where_clause + " AND " if where_clause else " WHERE ") + "category = 'Anomalous'"
    anomalous_count = query_one(f"SELECT COUNT(*) as c FROM predictions{where_anomalous}", tuple(params))["c"]

    where_unclass = (where_clause + " AND " if where_clause else " WHERE ") + "(category = 'Unclassified' OR category IS NULL)"
    unclassified_count = query_one(f"SELECT COUNT(*) as c FROM predictions{where_unclass}", tuple(params))["c"]

    # Calculate percentages: exclude unclassified from the three category percentages
    classified_total = normal_count + medium_count + anomalous_count
    normal_pct = round((normal_count / classified_total) * 100, 2) if classified_total > 0 else 0.0
    medium_pct = round((medium_count / classified_total) * 100, 2) if classified_total > 0 else 0.0
    anomalous_pct = round((anomalous_count / classified_total) * 100, 2) if classified_total > 0 else 0.0
    unclass_pct = round((unclassified_count / total_logs) * 100, 2) if total_logs > 0 else 0.0

    # Build 24-hour timeline with separate counts for Normal, Medium, Anomalous, and Unclassified
    timeline_24h = []
    timeline_cutoff = (now - timedelta(hours=24)).isoformat()
    raw_24h_events = query_all(
        "SELECT timestamp, category FROM predictions WHERE timestamp >= ? ORDER BY timestamp ASC",
        (timeline_cutoff,)
    )

    # Bin into 24 hourly buckets
    hourly_buckets = {}
    for h in range(24):
        slot_dt = now - timedelta(hours=(23 - h))
        slot_key = slot_dt.strftime("%Y-%m-%d %H:00")
        label = slot_dt.strftime("%H:00")
        hourly_buckets[slot_key] = {
            "hour": label,
            "slot": slot_key,
            "normal": 0,
            "medium": 0,
            "anomalous": 0,
            "unclassified": 0,
            "total": 0
        }

    for ev in raw_24h_events:
        ts_str = str(ev.get("timestamp") or "")
        cat = ev.get("category") or "Unclassified"
        try:
            # Parse ISO timestamp up to hour
            parsed_dt = datetime.fromisoformat(ts_str.replace("Z", ""))
            ev_slot = parsed_dt.strftime("%Y-%m-%d %H:00")
            if ev_slot in hourly_buckets:
                b = hourly_buckets[ev_slot]
                b["total"] += 1
                if cat == "Normal":
                    b["normal"] += 1
                elif cat == "Medium":
                    b["medium"] += 1
                elif cat == "Anomalous":
                    b["anomalous"] += 1
                else:
                    b["unclassified"] += 1
        except Exception:
            continue

    timeline_24h = list(hourly_buckets.values())

    # Active model
    active_model = query_one("SELECT id, name, algorithm, version FROM models WHERE is_active = 1")

    # Recent predictions (last 10)
    recent_query = f"""
        SELECT id, timestamp, category, is_anomaly, probability, risk_score, confidence,
               raw_log, model_name, explanation_summary
        FROM predictions
        {where_clause}
        ORDER BY timestamp DESC LIMIT 10
    """
    recent = query_all(recent_query, tuple(params))

    return jsonify({
        "time_range": time_range,
        "total_processed": total_logs,
        "total_logs": total_logs,
        "normal_count": normal_count,
        "normal_percentage": normal_pct,
        "medium_count": medium_count,
        "medium_percentage": medium_pct,
        "anomalous_count": anomalous_count,
        "anomalies_flagged": anomalous_count,
        "anomalous_percentage": anomalous_pct,
        "unclassified_count": unclassified_count,
        "unclassified_percentage": unclass_pct,
        "classified_total": classified_total,
        "timeline_24h": timeline_24h,
        "active_model": active_model,
        "recent_activity": recent,
        "has_data": total_logs > 0
    }), 200
