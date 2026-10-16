-- Smart-Log SQLite Database Schema

CREATE TABLE IF NOT EXISTS datasets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    format TEXT NOT NULL,
    row_count INTEGER DEFAULT 0,
    col_count INTEGER DEFAULT 0,
    columns_json TEXT,
    sample_json TEXT,
    status TEXT DEFAULT 'unconfigured',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dataset_configs (
    id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    target_column TEXT NOT NULL,
    normal_value TEXT NOT NULL,
    anomaly_value TEXT NOT NULL,
    feature_columns_json TEXT NOT NULL,
    timestamp_column TEXT,
    message_column TEXT,
    train_ratio REAL DEFAULT 0.70,
    val_ratio REAL DEFAULT 0.15,
    test_ratio REAL DEFAULT 0.15,
    stratified INTEGER DEFAULT 1,
    is_approved INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    algorithm TEXT NOT NULL,
    version TEXT NOT NULL,
    dataset_id TEXT,
    dataset_name TEXT,
    hyperparameters_json TEXT,
    metrics_json TEXT,
    feature_schema_json TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    is_active INTEGER DEFAULT 0,
    training_duration_seconds REAL DEFAULT 0.0,
    created_at TEXT NOT NULL
);

INSERT OR IGNORE INTO models (id, name, algorithm, version, feature_schema_json, artifact_path, is_active, created_at)
VALUES ('unclassified', 'Unclassified System Marker', 'none', '0.0', '{}', '', 0, '2026-01-01T00:00:00');

CREATE TABLE IF NOT EXISTS training_jobs (
    id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    algorithm TEXT NOT NULL,
    status TEXT NOT NULL,
    progress INTEGER DEFAULT 0,
    message TEXT,
    model_id TEXT,
    error_message TEXT,
    started_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS predictions (
    id TEXT PRIMARY KEY,
    batch_id TEXT,
    model_id TEXT,
    model_name TEXT,
    model_version TEXT,
    raw_log TEXT NOT NULL,
    parsed_fields_json TEXT,
    features_json TEXT,
    prediction INTEGER,
    probability REAL,
    is_anomaly INTEGER NOT NULL DEFAULT 0,
    category TEXT NOT NULL DEFAULT 'Unclassified',
    risk_score REAL,
    confidence REAL,
    explanation_summary TEXT,
    observed_facts_json TEXT,
    model_explanation_json TEXT,
    security_interpretation TEXT,
    shap_values_json TEXT,
    timestamp TEXT NOT NULL,
    channel TEXT,
    record_id INTEGER,
    event_id INTEGER,
    provider TEXT,
    severity_label TEXT,
    FOREIGN KEY(model_id) REFERENCES models(id)
);

CREATE TABLE IF NOT EXISTS collector_checkpoints (
    channel TEXT PRIMARY KEY,
    last_record_id INTEGER DEFAULT 0,
    last_event_time TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    details_json TEXT,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(timestamp);
CREATE INDEX IF NOT EXISTS idx_predictions_is_anomaly ON predictions(is_anomaly);
CREATE INDEX IF NOT EXISTS idx_predictions_category ON predictions(category);
CREATE INDEX IF NOT EXISTS idx_predictions_batch_id ON predictions(batch_id);
CREATE INDEX IF NOT EXISTS idx_predictions_channel ON predictions(channel);
CREATE INDEX IF NOT EXISTS idx_predictions_provider ON predictions(provider);
CREATE UNIQUE INDEX IF NOT EXISTS idx_predictions_channel_record ON predictions(channel, record_id) WHERE channel IS NOT NULL AND record_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_models_is_active ON models(is_active);
