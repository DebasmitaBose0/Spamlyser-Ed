"""Shared fixtures and configuration for the Spamlyser test suite."""

import json
import tempfile
from pathlib import Path

import pytest

SAMPLE_MESSAGES = {
    "spam": [
        "WINNER!! You've won a FREE ticket to the Bahamas! Call 09061213087 now!",
        "URGENT: Your account has been compromised. Click here to verify: http://evil.phish",
        "Congratulations! You've been selected for a $1000 gift card. Reply YES to claim.",
        "Hey, I'm stuck in London and lost my wallet. Please send $500 via Western Union to help.",
        "Limited time offer! 0% APR on all credit cards. Apply now at https://scam-bank.com",
    ],
    "ham": [
        "Hey, are we still meeting for coffee tomorrow at 3pm?",
        "The report is ready for review. I've attached it to the email.",
        "Don't forget to pick up milk and bread on your way home.",
        "Thanks for your help with the project! Really appreciate it.",
        "Reminder: Team standup is at 9:30 AM in conference room B.",
    ],
    "edge": [
        "",
        "A" * 1001,
        "normal text with no special chars",
        "   ",
        "+1 (555) 123-4567",
    ],
}


@pytest.fixture(scope="session")
def sample_spam_messages():
    return list(SAMPLE_MESSAGES["spam"])


@pytest.fixture(scope="session")
def sample_ham_messages():
    return list(SAMPLE_MESSAGES["ham"])


@pytest.fixture(scope="session")
def sample_edge_messages():
    return list(SAMPLE_MESSAGES["edge"])


@pytest.fixture(scope="session")
def all_sample_messages():
    return [
        *SAMPLE_MESSAGES["spam"],
        *SAMPLE_MESSAGES["ham"],
        *SAMPLE_MESSAGES["edge"],
    ]


@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def temp_json_file(temp_data_dir):
    path = temp_data_dir / "test_data.json"
    path.write_text(json.dumps({"key": "value"}), encoding="utf-8")
    return path


@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("SPAMLYSER_DATA_DIR", str(tempfile.gettempdir()))
    monkeypatch.setenv("SPAMLYSER_MAX_SMS_LENGTH", "1000")
    monkeypatch.setenv("SPAMLYSER_ENABLE_TELEMETRY", "false")
