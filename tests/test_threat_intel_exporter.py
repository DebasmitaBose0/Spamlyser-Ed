"""Tests for threat intelligence export system."""

import json

from models.threat_intel_exporter import (
    build_stix_observation,
    build_stix_indicator,
    export_as_stix_bundle,
    export_as_csv,
    export_as_json_report,
)


SAMPLE_RECORDS = [
    {
        "message": "You won a free prize! Click here to claim",
        "label": "SPAM",
        "confidence": 0.95,
        "threat_type": "phishing",
        "sender": "+1234567890",
        "timestamp": "2026-01-01T00:00:00Z",
        "model_used": "ensemble",
    },
    {
        "message": "Hey, how are you?",
        "label": "HAM",
        "confidence": 0.12,
        "threat_type": "none",
        "sender": "+0987654321",
        "timestamp": "2026-01-01T00:01:00Z",
        "model_used": "ensemble",
    },
]


def test_build_stix_observation():
    obs = build_stix_observation(
        message="Test message",
        confidence=0.9,
        threat_type="phishing",
        sender="+111",
    )
    assert obs["type"] == "observed-data"
    assert obs["x_spamlyser_metadata"]["threat_type"] == "phishing"
    assert obs["x_spamlyser_metadata"]["confidence_score"] == 0.9


def test_build_stix_indicator():
    ind = build_stix_indicator(
        threat_type="phishing",
        confidence=0.9,
        indicator_pattern="[x-spam-classification:threat_type = 'phishing']",
    )
    assert ind["type"] == "indicator"
    assert "phishing" in ind["name"]
    assert ind["confidence"] == 90


def test_export_stix_bundle():
    bundle_json = export_as_stix_bundle(SAMPLE_RECORDS)
    bundle = json.loads(bundle_json)
    assert bundle["type"] == "bundle"
    assert len(bundle["objects"]) == 4  # 2 observations + 2 indicators


def test_export_csv():
    csv_output = export_as_csv(SAMPLE_RECORDS)
    assert "timestamp" in csv_output
    assert "SPAM" in csv_output
    assert "HAM" in csv_output
    lines = csv_output.strip().split("\n")
    assert len(lines) == 3  # header + 2 records


def test_export_csv_empty():
    assert export_as_csv([]) == ""


def test_export_json_report():
    report_json = export_as_json_report(SAMPLE_RECORDS)
    report = json.loads(report_json)
    assert report["report_metadata"]["record_count"] == 2
    assert "statistics" in report
    assert report["statistics"]["spam_count"] == 1
    assert report["statistics"]["ham_count"] == 1


def test_export_json_report_no_stats():
    report_json = export_as_json_report(SAMPLE_RECORDS, include_stats=False)
    report = json.loads(report_json)
    assert "statistics" not in report


def test_export_json_empty():
    report_json = export_as_json_report([])
    report = json.loads(report_json)
    assert report["report_metadata"]["record_count"] == 0
    assert "statistics" not in report


def test_stix_bundle_structure():
    bundle_json = export_as_stix_bundle(SAMPLE_RECORDS)
    bundle = json.loads(bundle_json)
    for obj in bundle["objects"]:
        assert "id" in obj
        assert "created" in obj
        assert "modified" in obj
