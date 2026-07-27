import json
import logging
import os
import time
import uuid
from datetime import datetime

class TelemetryLogger:
    """TelemetryLogger — Structured JSON-format diagnostic and performance logging engine."""
    _logger = None

    @classmethod
    def get_logger(cls):
        if cls._logger is None:
            cls._logger = logging.getLogger("spamlyser.telemetry")
            cls._logger.setLevel(logging.INFO)
            if not cls._logger.handlers:
                os.makedirs("data", exist_ok=True)
                handler = logging.FileHandler("data/telemetry.jsonl", encoding="utf-8")
                formatter = logging.Formatter("%(message)s")
                handler.setFormatter(formatter)
                cls._logger.addHandler(handler)
        return cls._logger

    @classmethod
    def log_event(cls, event_name: str, payload: dict = None):
        if payload is None:
            payload = {}
        log_entry = {
            "event": event_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": str(uuid.uuid4()),
            **payload
        }
        cls.get_logger().info(json.dumps(log_entry))

    @classmethod
    def log_execution_time(cls, name: str, start_time: float, success: bool = True, details: dict = None):
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        payload = {
            "name": name,
            "duration_ms": round(duration_ms, 2),
            "success": success,
        }
        if details:
            payload.update(details)
        cls.log_event("execution_telemetry", payload)
