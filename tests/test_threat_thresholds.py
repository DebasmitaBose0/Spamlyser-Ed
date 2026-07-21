import pytest
from models.threat_thresholds import ThreatThresholdManager


def test_threat_threshold_default_filter():
    manager = ThreatThresholdManager()
    threats = {
        "phishing": 0.75,       # >= 0.70 (keep)
        "scam_urgent": 0.60,    # < 0.65 (drop)
        "financial_fraud": 0.80 # >= 0.75 (keep)
    }
    filtered = manager.filter_threats(threats)
    assert "phishing" in filtered
    assert "financial_fraud" in filtered
    assert "scam_urgent" not in filtered


def test_threat_threshold_custom_setting():
    manager = ThreatThresholdManager()
    manager.set_threshold("scam_urgent", 0.50)
    threats = {"scam_urgent": 0.60}
    filtered = manager.filter_threats(threats)
    assert "scam_urgent" in filtered


def test_threat_threshold_invalid_range():
    manager = ThreatThresholdManager()
    with pytest.raises(ValueError):
        manager.set_threshold("phishing", 1.5)
