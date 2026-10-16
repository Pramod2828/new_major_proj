import os
import sys
import tempfile
import pytest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.config import Config
from backend.database.db import init_db
from backend.app import create_app

@pytest.fixture(scope="session")
def test_temp_dir():
    """Create a temporary directory for test artifacts and SQLite db."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture(scope="session")
def test_db_path(test_temp_dir):
    """Path to test SQLite database."""
    db_path = os.path.join(test_temp_dir, "test_smartlog.db")
    init_db(db_path)
    return db_path

@pytest.fixture
def app(test_temp_dir, test_db_path):
    """Test Flask application configured with temporary storage."""
    class TestConfig(Config):
        TESTING = True
        DATABASE_PATH = test_db_path
        UPLOAD_FOLDER = os.path.join(test_temp_dir, "uploads")
        ARTIFACT_FOLDER = os.path.join(test_temp_dir, "artifacts")
        LOG_FOLDER = os.path.join(test_temp_dir, "logs")

    TestConfig.init_directories()
    app = create_app(TestConfig)
    return app

@pytest.fixture
def client(app):
    """Test Flask client."""
    return app.test_client()
