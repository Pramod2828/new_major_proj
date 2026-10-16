import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path
from backend.config import Config

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

def dict_factory(cursor, row):
    """Convert SQLite row to Python dict."""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_connection(db_path=None):
    """Get a raw SQLite connection with row factory enabled."""
    path = db_path or Config.DATABASE_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def get_db(db_path=None):
    """Context manager for SQLite database transactions."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db(db_path=None):
    """Initialize database tables using schema.sql, apply schema migrations, and seed built-in datasets."""
    path = db_path or Config.DATABASE_PATH
    Config.init_directories()
    with get_db(path) as conn:
        _run_migrations(conn)
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_script = f.read()
        conn.executescript(schema_script)

    # Seed built-in AIT-LDS datasets (idempotent — skips already-present rows)
    try:
        from backend.dataset.builtin_seeder import seed_builtin_datasets
        seeded = seed_builtin_datasets()
        if seeded:
            import logging
            logging.getLogger("smartlog.db").info("Seeded %d built-in datasets into datasets table.", seeded)
    except Exception as _seed_err:
        import logging
        logging.getLogger("smartlog.db").warning("Could not seed built-in datasets: %s", _seed_err)

    return True

def _run_migrations(conn):
    """Ensure newly added columns exist in existing SQLite database tables."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='predictions';")
    if not cursor.fetchone():
        return

    cursor.execute("PRAGMA table_info(predictions);")
    existing_cols = {row["name"] for row in cursor.fetchall()}

    needed_cols = [
        ("category", "TEXT NOT NULL DEFAULT 'Unclassified'"),
        ("risk_score", "REAL"),
        ("confidence", "REAL"),
        ("explanation_summary", "TEXT"),
        ("observed_facts_json", "TEXT"),
        ("model_explanation_json", "TEXT"),
        ("security_interpretation", "TEXT"),
        ("channel", "TEXT"),
        ("record_id", "INTEGER"),
        ("event_id", "INTEGER"),
        ("provider", "TEXT"),
        ("severity_label", "TEXT"),
    ]
    for col_name, col_type in needed_cols:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE predictions ADD COLUMN {col_name} {col_type};")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS collector_checkpoints (
            channel TEXT PRIMARY KEY,
            last_record_id INTEGER DEFAULT 0,
            last_event_time TEXT,
            updated_at TEXT
        );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_channel ON predictions(channel);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_provider ON predictions(provider);")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_predictions_channel_record ON predictions(channel, record_id) WHERE channel IS NOT NULL AND record_id IS NOT NULL;")

    # Ensure unclassified marker model exists for foreign key and not-null safety
    cursor.execute("""
        INSERT OR IGNORE INTO models (id, name, algorithm, version, feature_schema_json, artifact_path, is_active, created_at)
        VALUES ('unclassified', 'Unclassified / System', 'none', '0.0', '{}', '', 0, '2026-01-01T00:00:00');
    """)



def query_all(query, params=(), db_path=None):
    """Execute a read query and return all rows as list of dicts."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

def query_one(query, params=(), db_path=None):
    """Execute a read query and return one row or None."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

def execute_write(query, params=(), db_path=None):
    """Execute an INSERT/UPDATE/DELETE query and return lastrowid / rowcount."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.lastrowid
