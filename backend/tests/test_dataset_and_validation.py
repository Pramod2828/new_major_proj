import os
import json
import pytest
import pandas as pd
from backend.dataset.loader import DatasetLoader
from backend.dataset.inspector import DatasetInspector
from backend.dataset.validator import DatasetValidator

# SYNTHETIC TEST FIXTURE: Small mocked dataset strictly for unit testing code paths
@pytest.fixture
def synthetic_csv_file(tmp_path):
    csv_file = tmp_path / "mock_server_logs.csv"
    data = {
        "timestamp": ["2026-02-10 12:00:01", "2026-02-10 12:00:02", "2026-02-10 12:00:03", "2026-02-10 12:00:04"] * 10,
        "service": ["sshd", "nginx", "kernel", "sudo"] * 10,
        "message_length": [45, 120, 85, 30] * 10,
        "severity_level": [6, 4, 3, 2] * 10,
        "is_error": [0, 1, 1, 0] * 10,
        "label": ["Normal", "Normal", "Anomaly", "Normal"] * 10  # 30 Normal, 10 Anomaly
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_file, index=False)
    return str(csv_file)

@pytest.fixture
def synthetic_json_file(tmp_path):
    json_file = tmp_path / "mock_logs.json"
    records = [
        {"host": "srv-1", "msg_len": 50, "status": "Normal"},
        {"host": "srv-2", "msg_len": 150, "status": "Anomaly"},
        {"host": "srv-1", "msg_len": 60, "status": "Normal"}
    ] * 10
    with open(json_file, "w") as f:
        json.dump(records, f)
    return str(json_file)

def test_dataset_loader_csv(synthetic_csv_file):
    df, meta = DatasetLoader.load(synthetic_csv_file)
    assert len(df) == 40
    assert "label" in df.columns
    assert meta["format"] == "csv"
    assert meta["loaded_rows"] == 40

def test_dataset_loader_json(synthetic_json_file):
    df, meta = DatasetLoader.load(synthetic_json_file)
    assert len(df) == 30
    assert "status" in df.columns
    assert meta["format"] == "json"

def test_dataset_inspector(synthetic_csv_file):
    df, _ = DatasetLoader.load(synthetic_csv_file)
    inspection = DatasetInspector.inspect(df, sample_size=5)

    assert inspection["total_rows"] == 40
    assert inspection["total_columns"] == 6
    assert len(inspection["columns"]) == 6
    assert len(inspection["preview_records"]) == 5

    # Check candidate target detection
    target_names = [t["column"] for t in inspection["candidate_targets"]]
    assert "label" in target_names

def test_dataset_validator_success(synthetic_csv_file):
    df, _ = DatasetLoader.load(synthetic_csv_file)
    config = {
        "target_column": "label",
        "normal_value": "Normal",
        "anomaly_value": "Anomaly",
        "feature_columns": ["message_length", "severity_level", "is_error", "service"],
        "train_ratio": 0.70,
        "val_ratio": 0.15,
        "test_ratio": 0.15,
        "stratified": True
    }
    is_valid, errors, warnings = DatasetValidator.validate_configuration(df, config)
    assert is_valid is True
    assert len(errors) == 0

def test_dataset_validator_target_leakage(synthetic_csv_file):
    df, _ = DatasetLoader.load(synthetic_csv_file)
    config = {
        "target_column": "label",
        "normal_value": "Normal",
        "anomaly_value": "Anomaly",
        "feature_columns": ["message_length", "label"],  # LEAKAGE!
        "train_ratio": 0.70,
        "val_ratio": 0.15,
        "test_ratio": 0.15
    }
    is_valid, errors, _ = DatasetValidator.validate_configuration(df, config)
    assert is_valid is False
    assert any("LEAKAGE" in err for err in errors)

def test_dataset_validator_missing_class(synthetic_csv_file):
    df, _ = DatasetLoader.load(synthetic_csv_file)
    config = {
        "target_column": "label",
        "normal_value": "Normal",
        "anomaly_value": "NonExistentAnomaly",
        "feature_columns": ["message_length"],
        "train_ratio": 0.70,
        "val_ratio": 0.15,
        "test_ratio": 0.15
    }
    is_valid, errors, _ = DatasetValidator.validate_configuration(df, config)
    assert is_valid is False
    assert any("was not found in column" in err for err in errors)
