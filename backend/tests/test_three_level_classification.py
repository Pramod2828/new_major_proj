import math
import json
import pytest
import numpy as np
from datetime import datetime

from backend.database.db import init_db, get_db, query_all, query_one
from backend.services.classification_policy import RiskClassificationPolicy
from backend.services.inference_service import InferenceService
from backend.models.random_forest.rf_classifier import RandomForestModelWrapper
from backend.preprocessing.pipeline import PreprocessingBundle
from backend.models.registry import ModelRegistry
from backend.reports.pdf_generator import PDFReportGenerator
from backend.reports.csv_exporter import CSVExporter

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Isolate database to tmp_path for clean tests."""
    test_db = tmp_path / "test_smartlog.db"
    from backend.config import Config
    monkeypatch.setattr(Config, "DATABASE_PATH", str(test_db))
    monkeypatch.setattr(Config, "ARTIFACT_FOLDER", str(tmp_path / "artifacts"))
    monkeypatch.setattr(Config, "UPLOAD_FOLDER", str(tmp_path / "uploads"))
    Config.init_directories()
    init_db(str(test_db))
    yield
    # Cleanup ModelRegistry active model cache
    with get_db() as conn:
        conn.execute("UPDATE models SET is_active = 0")

def test_risk_classification_policy_categories():
    """Test standard probability mapping to Normal, Medium, and Anomalous categories."""
    policy = RiskClassificationPolicy(threshold_normal=0.30, threshold_anomaly=0.70)

    # Low risk -> Normal
    assert policy.classify(0.0) == "Normal"
    assert policy.classify(0.15) == "Normal"
    assert policy.classify(0.2999) == "Normal"

    # Borderline risk -> Medium
    assert policy.classify(0.30) == "Medium"
    assert policy.classify(0.50) == "Medium"
    assert policy.classify(0.6999) == "Medium"

    # High risk -> Anomalous
    assert policy.classify(0.70) == "Anomalous"
    assert policy.classify(0.85) == "Anomalous"
    assert policy.classify(1.0) == "Anomalous"

def test_risk_classification_policy_threshold_boundaries():
    """Test exact threshold boundary conditions and custom threshold validation."""
    policy = RiskClassificationPolicy(threshold_normal=0.25, threshold_anomaly=0.75)
    assert policy.threshold_normal == 0.25
    assert policy.threshold_anomaly == 0.75

    # Boundary checks
    assert policy.classify(0.249) == "Normal"
    assert policy.classify(0.25) == "Medium"
    assert policy.classify(0.749) == "Medium"
    assert policy.classify(0.75) == "Anomalous"

    # Invalid thresholds must raise ValueError
    with pytest.raises(ValueError):
        RiskClassificationPolicy(threshold_normal=0.80, threshold_anomaly=0.20)
    with pytest.raises(ValueError):
        RiskClassificationPolicy(threshold_normal=-0.1, threshold_anomaly=0.70)
    with pytest.raises(ValueError):
        RiskClassificationPolicy(threshold_normal=0.30, threshold_anomaly=1.5)

def test_risk_classification_policy_missing_probabilities():
    """Test missing or invalid probabilities default to Unclassified."""
    policy = RiskClassificationPolicy()

    assert policy.classify(None) == "Unclassified"
    assert policy.classify(float("nan")) == "Unclassified"
    assert policy.classify("not_a_number") == "Unclassified"
    assert policy.calculate_confidence(None) is None
    assert policy.calculate_confidence(float("nan")) is None

def test_structured_explanation_generation():
    """Verify separate generation of observed facts, model explanation, and security interpretations."""
    policy = RiskClassificationPolicy()
    record = {
        "timestamp": "2026-10-13T10:00:00",
        "hostname": "server01",
        "service": "sshd",
        "severity": 3,
        "raw": "Failed password for root from 192.168.1.50 port 22",
        "message": "Failed password for root from 192.168.1.50 port 22"
    }
    features = {
        "entropy": 3.8,
        "token_count": 8,
        "has_error": 1,
        "has_failed_auth": 1,
        "has_auth": 1,
        "has_denied": 0,
        "has_warning": 0,
        "source_ip": "192.168.1.50",
        "username": "root"
    }

    # Test Anomalous explanation
    exp = policy.build_explanation(
        record=record,
        features=features,
        category="Anomalous",
        probability=0.88,
        confidence=0.76,
        original_prediction=1,
        shap_data=None,
        model_meta={"name": "Test RF", "algorithm": "random_forest", "version": "1.0"}
    )

    # 1. Observed facts
    assert "observed_facts" in exp
    assert exp["observed_facts"]["application_name"] == "sshd"
    assert exp["observed_facts"]["hostname"] == "server01"
    assert exp["observed_facts"]["log_level"] == "ERROR"
    assert exp["observed_facts"]["has_failed_auth_flag"] is True

    # 2. Model explanation
    assert "model_explanation" in exp
    assert exp["model_explanation"]["risk_score_probability"] == 0.88
    assert exp["model_explanation"]["original_prediction"] == 1
    assert "≥ 70.0%" in exp["model_explanation"]["decision_rationale"]

    # 3. Security interpretation (must not claim confirmed attack)
    assert "security_interpretation" in exp
    assert "not a confirmed attack" in exp["security_interpretation"]

    # Test Unclassified explanation
    unclass_exp = policy.build_explanation(
        record=record,
        features=features,
        category="Unclassified",
        probability=None,
        confidence=None,
        original_prediction=None
    )
    assert "Unclassified" in unclass_exp["summary"]
    assert "cannot be performed without valid model probability" in unclass_exp["model_explanation"]["uncertainty_note"]

def test_validation_set_policy_evaluation():
    """Verify validation set probability distribution and precision metric calculation."""
    policy = RiskClassificationPolicy(threshold_normal=0.30, threshold_anomaly=0.70)
    y_val = [0, 0, 0, 0, 1, 1, 1, 1, 1, 1]
    y_probs = [0.10, 0.15, 0.20, 0.45, 0.55, 0.65, 0.75, 0.85, 0.90, 0.95]

    res = policy.validate_on_validation_set(y_val, y_probs)
    assert res["validated"] is True
    assert res["total_validation_samples"] == 10
    assert res["distribution"]["normal_count"] == 3
    assert res["distribution"]["medium_count"] == 3
    assert res["distribution"]["anomalous_count"] == 4
    # All 4 in anomalous are true anomalies
    assert res["anomalous_precision"] == 1.0

def test_inference_no_active_model_records_unclassified():
    """When no active model is present and allow_unclassified=True, inference records logs as Unclassified."""
    raw_logs = [
        "<34>Oct 11 22:14:15 server01 sshd[1234]: Failed password for root from 192.168.1.50 port 22",
        "<13>Oct 11 22:14:18 server01 sshd[1234]: Accepted publickey for ubuntu from 10.0.0.1 port 54321"
    ]
    res = InferenceService.predict_logs(raw_lines=raw_logs, allow_unclassified=True)

    assert res["success"] is True
    assert res["has_active_model"] is False
    assert res["total_processed"] == 2
    assert res["unclassified_count"] == 2
    assert res["normal_count"] == 0
    assert res["anomalous_count"] == 0

    # Verify SQLite records
    rows = query_all("SELECT * FROM predictions")
    assert len(rows) == 2
    for r in rows:
        assert r["category"] == "Unclassified"
        assert r["probability"] is None
        assert r["risk_score"] is None
        assert "Unclassified event" in r["explanation_summary"]

def test_inference_three_level_classification_with_active_model(tmp_path):
    """Test live inference with active model deriving Normal, Medium, and Anomalous categories."""
    import pandas as pd
    from backend.preprocessing.pipeline import PreprocessingBundle

    # Create synthetic dataset & bundle
    df_train = pd.DataFrame([
        {"message_length": 50, "token_count": 8, "digit_ratio": 0.1, "entropy": 2.5, "severity_level": 6, "has_error": 0, "has_warning": 0, "has_auth": 1, "has_failed_auth": 0, "has_denied": 0, "has_ip": 1, "service": "sshd", "hostname": "host1"},
        {"message_length": 60, "token_count": 10, "digit_ratio": 0.2, "entropy": 2.8, "severity_level": 6, "has_error": 0, "has_warning": 0, "has_auth": 0, "has_failed_auth": 0, "has_denied": 0, "has_ip": 0, "service": "systemd", "hostname": "host1"},
        {"message_length": 120, "token_count": 15, "digit_ratio": 0.4, "entropy": 4.5, "severity_level": 2, "has_error": 1, "has_warning": 0, "has_auth": 1, "has_failed_auth": 1, "has_denied": 1, "has_ip": 1, "service": "sshd", "hostname": "host1"},
        {"message_length": 130, "token_count": 16, "digit_ratio": 0.5, "entropy": 4.8, "severity_level": 3, "has_error": 1, "has_warning": 1, "has_auth": 1, "has_failed_auth": 1, "has_denied": 1, "has_ip": 1, "service": "sudo", "hostname": "host1"},
    ] * 5)
    y_train = np.array([0, 0, 1, 1] * 5)

    feature_cols = list(df_train.columns)
    bundle = PreprocessingBundle.infer_and_create(df_train, feature_cols)
    X_train_trans = bundle.fit_transform(df_train)

    rf_model = RandomForestModelWrapper(model_id="test_rf_model", hyperparameters={"n_estimators": 10, "random_state": 42})
    rf_model.feature_names = bundle.transformed_feature_names
    rf_model.fit(X_train_trans, y_train)

    # Save and activate
    saved = ModelRegistry.save_model(
        model_wrapper=rf_model,
        preprocessor=bundle,
        metrics={"accuracy": 1.0, "classification_policy": {"threshold_normal": 0.30, "threshold_anomaly": 0.70}},
        dataset_meta={"name": "Synthetic SOC Dataset"}
    )
    mid = saved.get("id") or saved.get("model_id")
    ModelRegistry.activate_model(mid)

    # Test logs
    normal_log = "<13>Oct 11 22:14:18 server01 sshd[1234]: Accepted publickey for ubuntu from 10.0.0.1 port 54321"
    anomaly_log = "<34>Oct 11 22:14:15 server01 sshd[1234]: Failed password for root from 192.168.1.50 port 22 denied error"

    res = InferenceService.predict_logs(raw_lines=[normal_log, anomaly_log])
    assert res["success"] is True
    assert res["has_active_model"] is True
    assert len(res["results"]) == 2

    r_norm = res["results"][0]
    r_anom = res["results"][1]

    assert r_norm["category"] in ("Normal", "Medium")
    assert r_anom["category"] in ("Medium", "Anomalous")
    assert r_norm["probability"] is not None
    assert r_norm["confidence"] is not None

    # Verify both prediction and category are saved separately
    saved_rows = query_all("SELECT prediction, category, risk_score, confidence FROM predictions WHERE model_id = ?", (saved["id"],))
    assert len(saved_rows) == 2
    for sr in saved_rows:
        assert sr["prediction"] in (0, 1)
        assert sr["category"] in ("Normal", "Medium", "Anomalous")
        assert sr["risk_score"] is not None

def test_inference_missing_probabilities_unclassified():
    """If classifier lacks predict_proba, events are categorized as Unclassified."""
    class DummyClassifierNoProba:
        def predict(self, X):
            return np.array([1] * len(X))

    # Mock custom policy with dummy model
    policy = RiskClassificationPolicy()
    cat = policy.classify(None, original_prediction=1)
    assert cat == "Unclassified"
    expl = policy.build_explanation(
        record={"raw": "test"},
        features={},
        category=cat,
        probability=None,
        confidence=None,
        original_prediction=1
    )
    assert "Unclassified" in expl["summary"]
    assert expl["model_explanation"]["original_prediction"] == 1
    assert expl["model_explanation"]["risk_score_probability"] is None

def test_reports_pdf_and_csv_three_level_exports():
    """Verify that PDF and CSV generators include all 3 categories and confidence scores."""
    predictions = [
        {"id": "p1", "timestamp": "2026-10-13T10:00:00", "category": "Normal", "is_anomaly": False, "probability": 0.12, "risk_score": 0.12, "confidence": 0.76, "raw_log": "normal msg", "explanation_summary": "Normal baseline operational event"},
        {"id": "p2", "timestamp": "2026-10-13T10:01:00", "category": "Medium", "is_anomaly": False, "probability": 0.52, "risk_score": 0.52, "confidence": 0.04, "raw_log": "borderline msg", "explanation_summary": "Borderline risk with conflicting signals"},
        {"id": "p3", "timestamp": "2026-10-13T10:02:00", "category": "Anomalous", "is_anomaly": True, "probability": 0.91, "risk_score": 0.91, "confidence": 0.82, "raw_log": "failed auth msg", "explanation_summary": "High risk anomaly authentication failure"},
        {"id": "p4", "timestamp": "2026-10-13T10:03:00", "category": "Unclassified", "is_anomaly": False, "probability": None, "risk_score": None, "confidence": None, "raw_log": "unclassified msg", "explanation_summary": "Unclassified due to missing probability"}
    ]
    stats = {
        "total_logs": 4,
        "normal_count": 1,
        "medium_count": 1,
        "anomalous_count": 1,
        "unclassified_count": 1
    }
    model_meta = {"name": "Test RF", "algorithm": "random_forest", "version": "1.0", "metrics": {}}

    # PDF generation
    pdf_bytes = PDFReportGenerator.generate_report(model_meta, predictions, stats)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000

    # CSV generation
    csv_str = CSVExporter.export_predictions(predictions)
    assert "Normal" in csv_str
    assert "Medium" in csv_str
    assert "Anomalous" in csv_str
    assert "Unclassified" in csv_str
    assert "risk_score" in csv_str
    assert "confidence" in csv_str
