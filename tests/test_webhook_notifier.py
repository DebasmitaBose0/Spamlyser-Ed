"""Tests for the enhanced WebhookNotifier with retry, circuit breaker, and history."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from models.webhook_notifier import (
    WebhookNotifier,
    CircuitBreakerState,
)


@pytest.fixture
def temp_config():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", encoding="utf-8", delete=False
    ) as f:
        json.dump({"webhooks": [], "history": []}, f)
        tmp = f.name
    yield tmp
    os.unlink(tmp)


def test_circuit_breaker_initially_closed():
    cb = CircuitBreakerState(threshold=3, reset_seconds=60)
    assert not cb.is_open()
    assert cb.should_attempt()


def test_circuit_breaker_opens_after_threshold():
    cb = CircuitBreakerState(threshold=3, reset_seconds=60)
    for _ in range(3):
        cb.record_failure()
    assert cb.is_open()
    assert not cb.should_attempt()


def test_circuit_breaker_records_success():
    cb = CircuitBreakerState(threshold=3, reset_seconds=60)
    cb.record_failure()
    cb.record_failure()
    cb.record_success()
    assert not cb.is_open()


def test_add_webhook_valid_url(temp_config):
    n = WebhookNotifier(config_path=temp_config)
    assert n.add_webhook("https://hooks.example.com/hook")
    webhooks = n.get_webhooks()
    assert len(webhooks) == 1
    assert webhooks[0]["url"] == "https://hooks.example.com/hook"


def test_add_webhook_invalid_url(temp_config):
    n = WebhookNotifier(config_path=temp_config)
    assert not n.add_webhook("not-a-url")
    assert len(n.get_webhooks()) == 0


def test_remove_webhook(temp_config):
    n = WebhookNotifier(config_path=temp_config)
    n.add_webhook("https://example.com/hook")
    assert n.remove_webhook("https://example.com/hook")
    assert len(n.get_webhooks()) == 0


def test_remove_nonexistent_webhook(temp_config):
    n = WebhookNotifier(config_path=temp_config)
    assert not n.remove_webhook("https://example.com/nope")


def test_update_webhook(temp_config):
    n = WebhookNotifier(config_path=temp_config)
    n.add_webhook("https://example.com/hook")
    assert n.update_webhook("https://example.com/hook", {"enabled": False})
    wh = n.get_webhooks()[0]
    assert not wh["enabled"]


def test_update_nonexistent_webhook(temp_config):
    n = WebhookNotifier(config_path=temp_config)
    assert not n.update_webhook("https://example.com/nope", {"enabled": False})


@patch("models.webhook_notifier.req.post")
def test_successful_delivery_records_history(mock_post, temp_config):
    mock_post.return_value = MagicMock(status_code=200)
    mock_post.return_value.raise_for_status = MagicMock()
    n = WebhookNotifier(config_path=temp_config, max_retries=1)
    n.add_webhook("https://example.com/hook")
    n.notify_spam_detected("test message", 0.95, threat_type="phishing")
    import time
    time.sleep(0.3)
    assert mock_post.called
    history = n.get_history()
    assert len(history) >= 1
    assert history[0]["status"] == "success"


@patch("models.webhook_notifier.req.post")
def test_failed_delivery_retries_and_records_failure(mock_post, temp_config):
    mock_post.side_effect = __import__("requests").RequestException("Server error")
    n = WebhookNotifier(config_path=temp_config, max_retries=2, base_delay=0.01)
    n.add_webhook("https://example.com/hook")
    n.notify_spam_detected("test", 0.9)
    import time
    time.sleep(0.5)
    assert mock_post.call_count >= 2
    history = n.get_history()
    failed = [h for h in history if h["status"] == "failed"]
    assert len(failed) >= 1


@patch("models.webhook_notifier.req.post")
def test_circuit_breaker_skips_after_repeated_failures(mock_post, temp_config):
    mock_post.side_effect = __import__("requests").RequestException("Server error")
    n = WebhookNotifier(config_path=temp_config, max_retries=1, base_delay=0.01)
    n.add_webhook("https://example.com/hook")
    for _ in range(6):
        n.notify_spam_detected("test", 0.9)
    import time
    time.sleep(0.5)
    history = n.get_history()
    skipped = [h for h in history if h["status"] == "skipped"]
    assert len(skipped) >= 1


@patch("models.webhook_notifier.req.post")
def test_delivery_stats_calculated_correctly(mock_post, temp_config):
    mock_post.return_value = MagicMock(status_code=200)
    mock_post.return_value.raise_for_status = MagicMock()
    n = WebhookNotifier(config_path=temp_config, max_retries=1)
    n.add_webhook("https://example.com/hook")
    n.notify_spam_detected("test", 0.9)
    import time
    time.sleep(0.3)
    stats = n.get_delivery_stats()
    assert stats["total_deliveries"] >= 1
    assert stats["successful"] >= 1


def test_get_history_filters(temp_config):
    n = WebhookNotifier(config_path=temp_config)
    n._add_history_entry({
        "webhook_url": "https://a.com", "event": "spam_detected", "status": "success"
    })
    n._add_history_entry({
        "webhook_url": "https://b.com", "event": "spam_detected", "status": "failed"
    })
    filtered = n.get_history(webhook_url="https://a.com")
    assert len(filtered) == 1
    assert filtered[0]["webhook_url"] == "https://a.com"
    filtered_status = n.get_history(status="failed")
    assert len(filtered_status) == 1
    filtered_event = n.get_history(event_type="spam_detected")
    assert len(filtered_event) == 2


def test_clear_history(temp_config):
    n = WebhookNotifier(config_path=temp_config)
    n._add_history_entry({"status": "success"})
    assert len(n.get_history()) >= 1
    n.clear_history()
    assert len(n.get_history()) == 0


@patch("models.webhook_notifier.req.post")
def test_webhook_disabled_does_not_send(mock_post, temp_config):
    n = WebhookNotifier(config_path=temp_config, max_retries=1)
    n.add_webhook("https://example.com/hook")
    n.update_webhook("https://example.com/hook", {"enabled": False})
    n.notify_spam_detected("test", 0.9)
    import time
    time.sleep(0.3)
    assert not mock_post.called


@patch("models.webhook_notifier.req.post")
def test_event_filtering_only_spam_events(mock_post, temp_config):
    n = WebhookNotifier(config_path=temp_config, max_retries=1)
    n.add_webhook("https://example.com/hook", events=["spam_detected"])
    n.notify_spam_detected("test", 0.9)
    import time
    time.sleep(0.3)
    assert mock_post.called


def test_persistence_across_reload(temp_config):
    n1 = WebhookNotifier(config_path=temp_config)
    n1.add_webhook("https://example.com/hook")
    n2 = WebhookNotifier(config_path=temp_config)
    assert len(n2.get_webhooks()) == 1
    assert n2.get_webhooks()[0]["url"] == "https://example.com/hook"


def test_history_persistence_across_reload(temp_config):
    n1 = WebhookNotifier(config_path=temp_config)
    n1._add_history_entry({
        "status": "success", "webhook_url": "https://a.com", "event": "test"
    })
    n2 = WebhookNotifier(config_path=temp_config)
    history = n2.get_history()
    assert len(history) >= 1
