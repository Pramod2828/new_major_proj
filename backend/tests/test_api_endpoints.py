import json
import pytest

def test_api_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["database"] is True

def test_api_system_status(client):
    res = client.get("/api/system/status")
    assert res.status_code == 200
    data = res.get_json()
    assert "counts" in data
    assert "system_resources" in data

def test_training_guard_initial_state(client):
    res = client.get("/api/training/guard")
    assert res.status_code == 200
    data = res.get_json()
    # Initially no datasets approved, so can_train should be False
    assert data["can_train"] is False
    assert "disabled" in data["message"]

def test_inference_without_active_model(client):
    # Ensure no active model is set
    from backend.database.db import execute_write
    execute_write("UPDATE models SET is_active = 0")

    # Predict without active model should return a clean error, not fake predictions
    res = client.post(
        "/api/inference/predict-logs",
        data=json.dumps({"logs": ["Failed password for root from 10.0.0.1"]}),
        content_type="application/json"
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert "No active model" in data["error"]

def test_reports_csv_export_endpoint(client):
    res = client.get("/api/reports/csv")
    assert res.status_code == 200
    assert "text/csv" in res.content_type
    # Should contain headers
    assert "id,timestamp,is_anomaly" in res.data.decode("utf-8")

def test_reports_pdf_export_endpoint(client):
    res = client.get("/api/reports/pdf")
    assert res.status_code == 200
    assert "application/pdf" in res.content_type
    assert len(res.data) > 0
