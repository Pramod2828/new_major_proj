import os
from pathlib import Path

class Config:
    """Smart-Log Backend Configuration."""
    BASE_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = BASE_DIR.parent

    # Database
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH",
        str(BASE_DIR / "database" / "smartlog.db")
    )

    # Directories
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER",
        str(BASE_DIR / "uploads")
    )
    ARTIFACT_FOLDER = os.environ.get(
        "ARTIFACT_FOLDER",
        str(BASE_DIR / "artifacts")
    )
    LOG_FOLDER = os.environ.get(
        "LOG_FOLDER",
        str(BASE_DIR / "logs")
    )

    # Security & Uploads
    SECRET_KEY = os.environ.get("SECRET_KEY", "smartlog-dev-secret-key-change-in-production")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 100 * 1024 * 1024))  # 100MB
    ALLOWED_DATASET_EXTENSIONS = {".csv", ".json", ".jsonl"}
    ALLOWED_LOG_EXTENSIONS = {".log", ".txt", ".json", ".csv"}

    # CORS
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")

    # Supported ML Algorithms
    SUPPORTED_ALGORITHMS = ["random_forest", "xgboost"]

    @classmethod
    def init_directories(cls):
        """Ensure all required folders exist."""
        for path in [
            cls.UPLOAD_FOLDER,
            cls.ARTIFACT_FOLDER,
            cls.LOG_FOLDER,
            os.path.dirname(cls.DATABASE_PATH),
        ]:
            os.makedirs(path, exist_ok=True)
