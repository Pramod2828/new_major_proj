import os
import sys
import logging
from flask import Flask, jsonify
from flask_cors import CORS

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from backend.config import Config
from backend.database.db import init_db
from backend.api.system_api import system_bp
from backend.api.dataset_api import dataset_bp
from backend.api.training_api import training_bp
from backend.api.model_api import model_bp
from backend.api.inference_api import inference_bp
from backend.api.reports_api import reports_bp
from backend.api.collector_api import collector_bp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("smartlog")

def create_app(config_class=Config):
    """Application factory for Smart-Log REST API."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize directories and SQLite schema
    config_class.init_directories()
    try:
        init_db()
        logger.info("SQLite database initialized successfully.")
    except Exception as e:
        logger.error("Database initialization failed: %s", str(e))

    # Configure CORS restricted to frontend origins
    CORS(app, resources={r"/api/*": {"origins": config_class.CORS_ORIGINS}})

    # Register blueprints
    app.register_blueprint(system_bp, url_prefix="/api")
    app.register_blueprint(dataset_bp, url_prefix="/api")
    app.register_blueprint(training_bp, url_prefix="/api")
    app.register_blueprint(model_bp, url_prefix="/api")
    app.register_blueprint(inference_bp, url_prefix="/api")
    app.register_blueprint(reports_bp, url_prefix="/api")
    app.register_blueprint(collector_bp, url_prefix="/api")

    # Start Windows Event background collector if not testing
    if not app.config.get("TESTING", False):
        try:
            from backend.collectors.windows_event_collector import get_windows_collector
            collector = get_windows_collector()
            collector.start()
            logger.info("Windows Event Log background collector started.")
        except Exception as e:
            logger.warning("Could not start Windows Event collector: %s", str(e))

    # Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad Request", "message": str(error.description if hasattr(error, 'description') else error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not Found", "message": "The requested endpoint was not found."}), 404

    @app.errorhandler(413)
    def request_too_large(error):
        return jsonify({"error": "Payload Too Large", "message": "The uploaded file exceeds the 100MB limit."}), 413

    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error("Internal server error: %s", str(error))
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred while processing your request."}), 500

    return app

if __name__ == "__main__":
    application = create_app()
    logger.info("Starting Smart-Log server on http://127.0.0.1:5000")
    application.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
