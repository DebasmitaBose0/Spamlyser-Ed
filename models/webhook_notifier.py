"""Webhook notification system for real-time SMS threat alerts.

Sends HTTP POST notifications to configured webhook URLs whenever
a message is classified as SPAM, enabling external integrations
(Slack, Discord, custom APIs, etc.). Supports retry with exponential
backoff, circuit breaker pattern, and event history tracking.
"""

import json
import logging
import os
import threading
import time
from collections import defaultdict
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

import requests as req

logger = logging.getLogger(__name__)

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_DELAY = 1.0
DEFAULT_RETRY_MAX_DELAY = 30.0
DEFAULT_CIRCUIT_BREAKER_THRESHOLD = 5
DEFAULT_CIRCUIT_BREAKER_RESET_SECONDS = 300
MAX_HISTORY_ENTRIES = 1000


class CircuitBreakerState:
    """Tracks failure state for a single webhook endpoint."""

    def __init__(self, threshold: int = DEFAULT_CIRCUIT_BREAKER_THRESHOLD,
                 reset_seconds: float = DEFAULT_CIRCUIT_BREAKER_RESET_SECONDS):
        self.threshold = threshold
        self.reset_seconds = reset_seconds
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.half_open_attempts = 0
        self._lock = threading.RLock()

    def record_failure(self) -> bool:
        """Returns True if the circuit should be opened."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            self.half_open_attempts = 0
            return self.failure_count >= self.threshold

    def record_success(self):
        with self._lock:
            self.failure_count = 0
            self.last_failure_time = None
            self.half_open_attempts = 0

    def is_open(self) -> bool:
        with self._lock:
            if self.failure_count < self.threshold:
                return False
            if self.last_failure_time is None:
                return False
            elapsed = time.time() - self.last_failure_time
            return elapsed < self.reset_seconds

    def should_attempt(self) -> bool:
        with self._lock:
            if self.failure_count < self.threshold:
                return True
            if self.last_failure_time is None:
                return True
            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.reset_seconds:
                self.half_open_attempts += 1
                return self.half_open_attempts <= 1
            return False


class WebhookNotifier:
    """Manages webhook endpoints and sends alerts asynchronously."""

    def __init__(
        self,
        config_path: str | None = None,
        max_retries: int | None = None,
        base_delay: float | None = None,
        max_delay: float | None = None,
    ):
        if config_path is None:
            config_path = os.getenv(
                "SPAMLYSER_WEBHOOK_CONFIG",
                str(Path(__file__).resolve().parent.parent / "data" / "webhooks.json"),
            )
        self._config_path = Path(config_path)
        self._webhooks: list[dict[str, Any]] = []
        self._history: list[dict[str, Any]] = []
        self._lock = threading.RLock()
        self._circuit_breakers: dict[str, CircuitBreakerState] = defaultdict(
            lambda: CircuitBreakerState()
        )
        self._max_retries = max_retries or int(
            os.getenv("SPAMLYSER_WEBHOOK_RETRY_COUNT", str(DEFAULT_MAX_RETRIES))
        )
        self._base_delay = base_delay or float(
            os.getenv("SPAMLYSER_WEBHOOK_RETRY_DELAY", str(DEFAULT_RETRY_BASE_DELAY))
        )
        self._max_delay = max_delay or float(
            os.getenv("SPAMLYSER_WEBHOOK_RETRY_MAX_DELAY", str(DEFAULT_RETRY_MAX_DELAY))
        )
        self._load_config()

    def _load_config(self):
        if self._config_path.exists():
            try:
                raw = self._config_path.read_text(encoding="utf-8")
                data = json.loads(raw)
                with self._lock:
                    self._webhooks = data.get("webhooks", [])
                    self._history = data.get("history", [])
            except (json.JSONDecodeError, OSError):
                with self._lock:
                    self._webhooks = []
                    self._history = []

    def _save_config_locked(self):
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(
            json.dumps(
                {"webhooks": self._webhooks, "history": self._history[-MAX_HISTORY_ENTRIES:]},
                indent=2,
            ),
            encoding="utf-8",
        )

    def _save_config(self):
        with self._lock:
            self._save_config_locked()

    def _add_history_entry(self, entry: dict[str, Any]):
        with self._lock:
            self._history.append(entry)
            if len(self._history) > MAX_HISTORY_ENTRIES:
                self._history = self._history[-MAX_HISTORY_ENTRIES:]
            self._save_config_locked()

    def get_history(
        self,
        limit: int = 100,
        offset: int = 0,
        webhook_url: str | None = None,
        event_type: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            entries = list(self._history)
        if webhook_url:
            entries = [e for e in entries if e.get("webhook_url") == webhook_url]
        if event_type:
            entries = [e for e in entries if e.get("event") == event_type]
        if status:
            entries = [e for e in entries if e.get("status") == status]
        return entries[offset:offset + limit]

    def clear_history(self):
        with self._lock:
            self._history = []
        self._save_config()

    def add_webhook(
        self,
        url: str,
        secret: str | None = None,
        events: list[str] | None = None,
        label: str = "",
    ) -> bool:
        if not url.startswith(("http://", "https://")):
            return False
        webhook = {
            "url": url,
            "secret": secret,
            "events": events or ["spam_detected"],
            "label": label or url,
            "enabled": True,
            "created_at": datetime.now(UTC).isoformat(),
        }
        with self._lock:
            self._webhooks.append(webhook)
        self._save_config()
        return True

    def remove_webhook(self, url: str) -> bool:
        with self._lock:
            before = len(self._webhooks)
            self._webhooks = [w for w in self._webhooks if w["url"] != url]
            removed = len(self._webhooks) < before
        if removed:
            self._save_config()
        return removed

    def update_webhook(self, url: str, updates: dict[str, Any]) -> bool:
        with self._lock:
            for wh in self._webhooks:
                if wh["url"] == url:
                    wh.update(updates)
                    self._save_config()
                    return True
        return False

    def get_webhooks(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._webhooks)

    def notify_spam_detected(
        self,
        message: str,
        confidence: float,
        threat_type: str | None = None,
        sender: str | None = None,
    ) -> None:
        """Send spam alert to all enabled webhooks (async with retry)."""
        payload = {
            "event": "spam_detected",
            "timestamp": datetime.now(UTC).isoformat(),
            "message_snippet": message[:200],
            "confidence": confidence,
            "threat_type": threat_type,
            "sender": sender,
            "source": "Spamlyser Pro",
        }
        with self._lock:
            targets = [
                wh for wh in self._webhooks
                if wh.get("enabled", True)
                and "spam_detected" in wh.get("events", ["spam_detected"])
            ]
        for wh in targets:
            threading.Thread(
                target=self._send_with_retry,
                args=(wh, payload),
                daemon=True,
            ).start()

    def _send_with_retry(self, webhook: dict, payload: dict):
        cb = self._circuit_breakers[webhook["url"]]
        if not cb.should_attempt():
            logger.warning(
                "Circuit breaker open for %s; skipping delivery",
                webhook["url"],
            )
            self._add_history_entry({
                "webhook_url": webhook["url"],
                "webhook_label": webhook.get("label", ""),
                "event": payload["event"],
                "status": "skipped",
                "error": "Circuit breaker open",
                "timestamp": datetime.now(UTC).isoformat(),
            })
            self._save_config()
            return

        last_error = None
        for attempt in range(1, self._max_retries + 1):
            try:
                headers = {"Content-Type": "application/json"}
                if webhook.get("secret"):
                    headers["X-Webhook-Secret"] = webhook["secret"]
                resp = req.post(
                    webhook["url"],
                    json=payload,
                    headers=headers,
                    timeout=10,
                )
                resp.raise_for_status()
                cb.record_success()
                self._add_history_entry({
                    "webhook_url": webhook["url"],
                    "webhook_label": webhook.get("label", ""),
                    "event": payload["event"],
                    "status": "success",
                    "attempt": attempt,
                    "status_code": resp.status_code,
                    "timestamp": datetime.now(UTC).isoformat(),
                })
                self._save_config()
                return
            except req.RequestException as e:
                last_error = e
                logger.warning(
                    "Webhook %s attempt %d/%d failed: %s",
                    webhook["url"], attempt, self._max_retries, e,
                )
                if attempt < self._max_retries:
                    delay = min(
                        self._base_delay * (2 ** (attempt - 1)),
                        self._max_delay,
                    )
                    time.sleep(delay)

        cb.record_failure()
        self._add_history_entry({
            "webhook_url": webhook["url"],
            "webhook_label": webhook.get("label", ""),
            "event": payload["event"],
            "status": "failed",
            "attempt": self._max_retries,
            "error": str(last_error),
            "timestamp": datetime.now(UTC).isoformat(),
        })
        self._save_config()

    def get_delivery_stats(self) -> dict[str, Any]:
        """Get aggregate delivery statistics for all webhooks."""
        with self._lock:
            total = len(self._history)
            success = sum(1 for e in self._history if e.get("status") == "success")
            failed = sum(1 for e in self._history if e.get("status") == "failed")
            skipped = sum(1 for e in self._history if e.get("status") == "skipped")
            by_webhook: dict[str, dict[str, int]] = {}
            for e in self._history:
                url = e.get("webhook_url", "unknown")
                if url not in by_webhook:
                    by_webhook[url] = {"success": 0, "failed": 0, "skipped": 0, "total": 0}
                st = e.get("status", "unknown")
                if st in by_webhook[url]:
                    by_webhook[url][st] += 1
                by_webhook[url]["total"] += 1
            return {
                "total_deliveries": total,
                "successful": success,
                "failed": failed,
                "skipped": skipped,
                "success_rate": (success / total * 100) if total > 0 else 0.0,
                "by_webhook": by_webhook,
            }
