from flask import Blueprint, request, make_response, jsonify
from backend.models.registry import ModelRegistry
from backend.reports.pdf_generator import PDFReportGenerator
from backend.reports.csv_exporter import CSVExporter
from backend.database.db import query_all, query_one

reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/reports/pdf", methods=["GET"])
def download_pdf_report():
    """Generate and download executive PDF report."""
    active_model = ModelRegistry.get_active_model()
    predictions = query_all("SELECT * FROM predictions ORDER BY timestamp DESC LIMIT 50")
    
    total = query_one("SELECT COUNT(*) as c FROM predictions")["c"]
    normal = query_one("SELECT COUNT(*) as c FROM predictions WHERE category = 'Normal'")["c"]
    medium = query_one("SELECT COUNT(*) as c FROM predictions WHERE category = 'Medium'")["c"]
    anomalies = query_one("SELECT COUNT(*) as c FROM predictions WHERE category = 'Anomalous'")["c"]
    unclass = query_one("SELECT COUNT(*) as c FROM predictions WHERE category = 'Unclassified' OR category IS NULL")["c"]
    stats = {
        "total_logs": total,
        "normal_count": normal,
        "medium_count": medium,
        "anomalous_count": anomalies,
        "unclassified_count": unclass
    }

    try:
        pdf_bytes = PDFReportGenerator.generate_report(
            model_meta=active_model,
            predictions=predictions,
            stats=stats
        )

        response = make_response(pdf_bytes)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = "attachment; filename=smartlog_security_audit.pdf"
        return response
    except Exception as e:
        return jsonify({"error": f"Failed to render PDF: {str(e)}"}), 500

@reports_bp.route("/reports/csv", methods=["GET"])
def download_csv_export():
    """Export prediction records to CSV."""
    limit = int(request.args.get("limit", 1000))
    predictions = query_all("SELECT * FROM predictions ORDER BY timestamp DESC LIMIT ?", (limit,))

    csv_data = CSVExporter.export_predictions(predictions)

    response = make_response(csv_data)
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=smartlog_predictions.csv"
    return response
