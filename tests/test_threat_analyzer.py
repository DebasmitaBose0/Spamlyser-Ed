"""Tests for threat_analyzer — verifying regex patterns avoid false positives."""

import pytest

from models.threat_analyzer import classify_threat_type


class TestScamUrgentPattern:
    """The scam_urgent regex must not fire on semantically unconnected text."""

    def test_legitimate_inheritance_not_flagged(self):
        message = (
            "I inherited a million dollars from my grandmother. "
            "She said I should invest it wisely. "
            "Are you free to discuss this now?"
        )
        result = classify_threat_type(message)
        assert result["threat_type"] != "Scam/Fraud", (
            "legitimate inheritance mention should not trigger scam"
        )

    def test_actual_spam_triggered(self):
        message = "You won million dollars! Claim now!"
        result = classify_threat_type(message)
        assert result["is_threat"], "obvious scam should be flagged"

    def test_empty_message(self):
        result = classify_threat_type("")
        assert not result["is_threat"]

    def test_normal_text_not_flagged(self):
        message = "Hey, are we still meeting for coffee tomorrow?"
        result = classify_threat_type(message)
        assert not result["is_threat"]

    def test_threat_categories_not_empty(self):
        from models.threat_analyzer import THREAT_CATEGORIES

        assert len(THREAT_CATEGORIES) > 0
