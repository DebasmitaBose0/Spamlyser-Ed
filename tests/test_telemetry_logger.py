import os
import json
import time
from models.telemetry_logger import TelemetryLogger

def test_telemetry_logger_file_creation():
    TelemetryLogger.log_event("test_event_creation", {"foo": "bar"})
    assert os.path.exists("data/telemetry.jsonl")

def test_telemetry_logger_structure():
    TelemetryLogger.log_event("test_structure", {"status": "ok"})
    
    with open("data/telemetry.jsonl", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    last_line = lines[-1].strip()
    data = json.loads(last_line)
    
    assert data["event"] == "test_structure"
    assert "timestamp" in data
    assert "request_id" in data
    assert data["status"] == "ok"

def test_telemetry_execution_time():
    start = time.perf_counter()
    time.sleep(0.01)
    TelemetryLogger.log_execution_time("test_exec", start, success=True, details={"meta": "test"})
    
    with open("data/telemetry.jsonl", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    last_line = lines[-1].strip()
    data = json.loads(last_line)
    
    assert data["event"] == "execution_telemetry"
    assert data["name"] == "test_exec"
    assert data["duration_ms"] >= 10.0
    assert data["success"] is True
    assert data["meta"] == "test"
