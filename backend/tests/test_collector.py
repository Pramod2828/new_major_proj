import pytest
import json
from unittest.mock import patch, MagicMock
from backend.collectors.windows_event_collector import WindowsEventCollector
from backend.services.inference_service import InferenceService
from backend.database.db import get_connection, get_db

def test_collector_initialization():
    collector = WindowsEventCollector.get_instance()
    assert collector is not None
    assert "System" in collector.CHANNELS
    assert "Application" in collector.CHANNELS
    assert "Security" in collector.CHANNELS
    status = collector.get_status()
    assert "hostname" in status
    assert "status" in status
    assert "channels" in status
    assert "counts_24h" in status

def test_collector_api_status(client):
    response = client.get("/api/collector/status")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "hostname" in data
    assert "channels" in data
    assert "counts_24h" in data

def test_collector_api_events_list(client):
    response = client.get("/api/collector/events?time_range=24h&limit=50")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert "events" in data
    assert "total" in data
    assert isinstance(data["events"], list)

def test_collector_api_pause_resume(client):
    res_pause = client.post("/api/collector/pause")
    assert res_pause.status_code == 200
    data_pause = json.loads(res_pause.data)
    assert data_pause["is_paused"] is True

    res_resume = client.post("/api/collector/resume")
    assert res_resume.status_code == 200
    data_resume = json.loads(res_resume.data)
    assert data_resume["is_paused"] is False

def test_collector_xml_parsing():
    sample_xml = """
      <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
        <System>
          <Provider Name="TestProvider"/>
          <EventID>1001</EventID>
          <Level>4</Level>
          <TimeCreated SystemTime="2026-10-14T05:00:00.000000000Z"/>
          <EventRecordID>99999</EventRecordID>
          <Computer>DESKTOP-TEST</Computer>
        </System>
        <RenderingInfo Culture="en-US">
          <Message>Test Event Log Ingestion</Message>
          <Level>Information</Level>
        </RenderingInfo>
      </Event>
    """
    collector = WindowsEventCollector.get_instance()
    events = collector._parse_xml_events(sample_xml, "Application")
    assert len(events) == 1
    ev = events[0]
    assert ev["record_id"] == 99999
    assert ev["event_id"] == 1001
    assert ev["provider"] == "TestProvider"
    assert ev["message"] == "Test Event Log Ingestion"
    assert ev["severity_label"] == "Information"

def test_windows_events_ingestion_and_deduplication():
    import random
    unique_record_id = random.randint(500000000, 900000000)
    sample_event = {
        "channel": "System",
        "record_id": unique_record_id,
        "event_id": 7001,
        "provider": "ServiceControlManager",
        "severity_level": 4,
        "severity_label": "Information",
        "timestamp": "2026-10-14T05:00:00.000000Z",
        "computer": "TEST-PC",
        "message": f"User logon notification test {unique_record_id}",
        "raw_text": f"System event 7001: User logon notification test {unique_record_id}"
    }

    # First ingestion
    result1 = InferenceService.process_windows_events([sample_event])
    assert result1["success"] is True
    assert result1["processed"] == 1
    assert result1["inserted"] == 1

    # Second ingestion with same channel and record_id should be ignored (deduplicated)
    result2 = InferenceService.process_windows_events([sample_event])
    assert result2["success"] is True
    assert result2["processed"] == 1
    assert result2["inserted"] == 0
