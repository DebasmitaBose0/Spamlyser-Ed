"""Extended tests for SenderReputation with auto-flush, pagination, and aggregate stats."""

import json
import os
import tempfile
import time

import pytest

from models.sender_reputation import SenderReputation


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", encoding="utf-8", delete=False
    ) as f:
        json.dump({}, f)
        tmp = f.name
    yield tmp
    os.unlink(tmp)


def test_record_and_get_reputation(temp_db):
    sr = SenderReputation(db_path=temp_db)
    sr.record_analysis("+1234567890", True, 0.95, threat_type="phishing")
    rep = sr.get_reputation("+1234567890")
    assert rep["spam_count"] == 1
    assert rep["ham_count"] == 0
    assert rep["total_messages"] == 1
    assert rep["reputation_score"] < 0.5


def test_multiple_analyses_same_sender(temp_db):
    sr = SenderReputation(db_path=temp_db)
    sr.record_analysis("+1111111111", True, 0.9)
    sr.record_analysis("+1111111111", False, 0.2)
    sr.record_analysis("+1111111111", True, 0.8)
    rep = sr.get_reputation("+1111111111")
    assert rep["total_messages"] == 3
    assert rep["spam_count"] == 2
    assert rep["ham_count"] == 1


def test_top_spam_senders_ordered(temp_db):
    sr = SenderReputation(db_path=temp_db)
    for i in range(5):
        sender = f"+sender{i}"
        for _ in range(i + 1):
            sr.record_analysis(sender, True, 0.9)
    top = sr.get_top_spam_senders(limit=3)
    assert len(top) == 3
    assert top[0]["spam_count"] >= top[1]["spam_count"]


def test_get_all_senders_pagination(temp_db):
    sr = SenderReputation(db_path=temp_db)
    for i in range(10):
        sr.record_analysis(f"+user{i}", i % 2 == 0, 0.5)

    page1 = sr.get_all_senders(limit=5, offset=0)
    assert len(page1) == 5
    page2 = sr.get_all_senders(limit=5, offset=5)
    assert len(page2) == 5

    all_senders = page1 + page2
    urls = [s["sender"] for s in all_senders]
    assert len(set(urls)) == 10


def test_sender_count(temp_db):
    sr = SenderReputation(db_path=temp_db)
    assert sr.get_sender_count() == 0
    sr.record_analysis("+a", True, 0.9)
    sr.record_analysis("+b", False, 0.1)
    assert sr.get_sender_count() == 2


def test_aggregate_stats(temp_db):
    sr = SenderReputation(db_path=temp_db)
    stats = sr.get_aggregate_stats()
    assert stats["total_senders"] == 0

    sr.record_analysis("+a", True, 0.9)
    sr.record_analysis("+b", False, 0.1)
    sr.record_analysis("+a", True, 0.8)

    stats = sr.get_aggregate_stats()
    assert stats["total_senders"] == 2
    assert stats["total_messages"] == 3
    assert stats["total_spam"] == 2
    assert stats["total_ham"] == 1


def test_auto_flush_happens(temp_db):
    sr = SenderReputation(db_path=temp_db)
    sr._flush_interval = 0.01
    sr.record_analysis("+test", True, 0.9)
    time.sleep(0.05)
    # The auto_flush should have persisted the data
    with open(temp_db, encoding="utf-8") as f:
        data = json.load(f)
    assert "+test" in data


def test_persistence_across_reload(temp_db):
    sr1 = SenderReputation(db_path=temp_db)
    sr1.record_analysis("+persist", True, 0.95)
    sr1.flush()

    sr2 = SenderReputation(db_path=temp_db)
    rep = sr2.get_reputation("+persist")
    assert rep["total_messages"] == 1
    assert rep["spam_count"] == 1


def test_threat_type_tracking(temp_db):
    sr = SenderReputation(db_path=temp_db)
    sr.record_analysis("+phisher", True, 0.9, threat_type="phishing")
    sr.record_analysis("+phisher", True, 0.8, threat_type="phishing")
    sr.record_analysis("+scammer", True, 0.7, threat_type="scam")
    rep = sr.get_reputation("+phisher")
    assert rep["threat_types"] == {"phishing": 2}
    rep2 = sr.get_reputation("+scammer")
    assert rep2["threat_types"] == {"scam": 1}


def test_reputation_decay_with_mixed_behavior(temp_db):
    sr = SenderReputation(db_path=temp_db)
    sr.record_analysis("+mixed", True, 0.9)
    score_after_spam = sr.get_reputation("+mixed")["reputation_score"]
    sr.record_analysis("+mixed", False, 0.1)
    sr.record_analysis("+mixed", False, 0.2)
    score_after_ham = sr.get_reputation("+mixed")["reputation_score"]
    assert score_after_ham > score_after_spam
