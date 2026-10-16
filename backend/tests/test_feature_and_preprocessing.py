import pytest
import numpy as np
import pandas as pd
from backend.feature_engineering.log_parser import LogParser
from backend.preprocessing.pipeline import PreprocessingBundle

def test_rfc_3164_syslog_parsing():
    raw_log = "<34>Oct 11 22:14:15 server01 sshd[1234]: Failed password for root from 192.168.1.50 port 22 ssh2"
    record = LogParser.parse_line(raw_log)

    assert record["hostname"] == "server01"
    assert record["service"] == "sshd"
    assert record["pid"] == "1234"
    assert record["severity"] == 2  # 34 % 8 = 2 (critical)
    assert "Failed password" in record["message"]
    assert record["source_ip"] == "192.168.1.50"
    assert record["username"] == "root"

def test_json_log_parsing():
    raw_log = '{"timestamp": "2026-02-10T12:00:00Z", "hostname": "api-gateway", "service": "auth-service", "level": "error", "message": "unauthorized token from 10.0.0.1"}'
    record = LogParser.parse_line(raw_log)

    assert record["hostname"] == "api-gateway"
    assert record["service"] == "auth-service"
    assert record["severity"] == 3  # error
    assert "unauthorized token" in record["message"]

def test_feature_extraction():
    record = {
        "raw": "Failed password for admin from 192.168.1.10",
        "service": "sshd",
        "hostname": "srv-1",
        "severity": 3,
        "message": "Failed password for admin from 192.168.1.10"
    }
    feats = LogParser.extract_features(record)

    assert feats["has_error"] == 1
    assert feats["has_auth"] == 1
    assert feats["has_failed_auth"] == 1
    assert feats["has_ip"] == 1
    assert feats["source_ip"] == "192.168.1.10"
    assert feats["message_length"] > 0
    assert feats["entropy"] > 0.0

def test_preprocessing_pipeline_fit_and_transform():
    # SYNTHETIC TEST DATA
    train_df = pd.DataFrame({
        "msg_len": [10, 50, 100, 200, 30],
        "entropy": [2.1, 3.4, 4.2, 1.9, 3.1],
        "service": ["sshd", "nginx", "sshd", "kernel", "nginx"]
    })
    test_df = pd.DataFrame({
        "msg_len": [25, 150],
        "entropy": [2.5, 3.8],
        "service": ["sshd", "unknown_new_service"]  # Unseen category test!
    })

    bundle = PreprocessingBundle.infer_and_create(train_df, ["msg_len", "entropy", "service"])
    X_train_trans = bundle.fit_transform(train_df)

    assert bundle.is_fitted is True
    assert X_train_trans.shape[0] == 5
    assert len(bundle.transformed_feature_names) >= 3

    # Transform test set without fitting
    X_test_trans = bundle.transform(test_df)
    assert X_test_trans.shape[0] == 2
    assert X_test_trans.shape[1] == X_train_trans.shape[1]
    # Unseen category should be handled cleanly via handle_unknown='ignore'
    assert not np.isnan(X_test_trans).any()
