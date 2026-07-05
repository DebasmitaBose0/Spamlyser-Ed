"""Webhook notification system for real-time SMS threat alerts.

Sends HTTP POST notifications to configured webhook URLs whenever
a message is classified as SPAM, enabling external integrations
(Slack, Discord, custom APIs, etc.).

Includes an in-process retry scheduler with exponential back-off for
transient delivery failures.
"""

import json
import logging
import os
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

import requests as req

logger = logging.getLogger(__name__)

_RETRY_BACKOFF = [1, 4, 16, 64]  # seconds between each retry attempt
_MAX_RETRIES = len(_RETRY_BACKOFF)


class RetryEntry:
    """A single webhook delivery that failed and is queued for retry."""

    def __init__(
        self,
        webhook: dict,
        payload: dict,
        attempt: int = 0,
    ):
        self.webhook = webhook
        self.payload = payload
        self.attempt = attempt
        self.next_retry_at: float = time.time() + _RETRY_BACKOFF[attempt] if attempt < _MAX_RETRIES else 0.0
        self.delivered: bool = False
        self.last_error: str | None = None


class WebhookNotifier:
    """Manages webhook endpoints and sends alerts asynchronously."""

    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_path = os.getenv(
                "SPAMLYSER_WEBHOOK_CONFIG",
                str(Path(__file__).resolve().parent.parent / "data" / "webhooks.json"),
            )
        self._config_path = Path(config_path)
        self._webhooks: list[dict[str, Any]] = []
        self._load_config()
        self._retry_queue: list[RetryEntry] = []
        self._lock = threading.Lock()
        self._scheduler_thread: threading.Thread | None = None
        self._scheduler_stop = threading.Event()
        self._start_scheduler()

    # ── Scheduler ──────────────────────────────────────────────────────────

    def _start_scheduler(self) -> None:
        self._scheduler_stop.clear()
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop, daemon=True, name="wh-retry-scheduler"
        )
        self._scheduler_thread.start()

    def _scheduler_loop(self) -> None:
        while not self._scheduler_stop.is_set():
            now = time.time()
            to_retry: list[RetryEntry] = []
            with self._lock:
                remaining: list[RetryEntry] = []
                for entry in self._retry_queue:
                    if entry.delivered:
                        continue
                    if entry.attempt >= _MAX_RETRIES:
                        logger.warning(
                            "Webhook %s exhausted retries: %s",
                            entry.webhook["url"],
                            entry.last_error,
                        )
                        continue
                    if now >= entry.next_retry_at:
                        to_retry.append(entry)
                    else:
                        remaining.append(entry)
                self._retry_queue = remaining

            for entry in to_retry:
                self._send_single(entry.webhook, entry.payload, entry)
            self._scheduler_stop.wait(2)

    @property
    def pending_retries(self) -> int:
        with self._lock:
            return sum(
                1 for e in self._retry_queue if not e.delivered
            )

    @property
    def retry_queue_size(self) -> int:
        with self._lock:
            return len(self._retry_queue)

    def get_retry_entries(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "url": e.webhook["url"],
                    "attempt": e.attempt,
                    "next_retry_at": e.next_retry_at,
                    "last_error": e.last_error,
                    "delivered": e.delivered,
                }
                for e in self._retry_queue
            ]

    def flush_retry_queue(self) -> int:
        with self._lock:
            count = len(self._retry_queue)
            self._retry_queue.clear()
            return count

    # ── Config persistence ─────────────────────────────────────────────────

    def _load_config(self):
        if self._config_path.exists():
            try:
                raw = self._config_path.read_text(encoding="utf-8")
                data = json.loads(raw)
                self._webhooks = data.get("webhooks", [])
            except (json.JSONDecodeError, OSError):
                self._webhooks = []

    def _save_config(self):
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(
            json.dumps({"webhooks": self._webhooks}, indent=2),
            encoding="utf-8",
        )

    # ── Webhook CRUD ───────────────────────────────────────────────────────

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
        self._webhooks.append(webhook)
        self._save_config()
        return True

    def remove_webhook(self, url: str) -> bool:
        before = len(self._webhooks)
        self._webhooks = [w for w in self._webhooks if w["url"] != url]
        if len(self._webhooks) < before:
            self._save_config()
            return True
        return False

    def get_webhooks(self) -> list[dict[str, Any]]:
        return list(self._webhooks)

    # ── Notification ───────────────────────────────────────────────────────

    def notify_spam_detected(
        self,
        message: str,
        confidence: float,
        threat_type: str | None = None,
        sender: str | None = None,
    ) -> None:
        """Send spam alert to all enabled webhooks (async)."""
        payload = {
            "event": "spam_detected",
            "timestamp": datetime.now(UTC).isoformat(),
            "message_snippet": message[:200],
            "confidence": confidence,
            "threat_type": threat_type,
            "sender": sender,
            "source": "Spamlyser Pro",
        }
        for wh in self._webhooks:
            if wh.get("enabled", True) and "spam_detected" in wh.get(
                "events", ["spam_detected"]
            ):
                threading.Thread(
                    target=self._send_single,
                    args=(wh, payload, None),
                    daemon=True,
                ).start()

    def _send_single(self, webhook: dict, payload: dict, retry_entry: RetryEntry | None = None):
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
            if retry_entry:
                retry_entry.delivered = True
                logger.info("Retry succeeded for %s", webhook["url"])
        except req.RequestException as e:
            error_msg = str(e)
            logger.warning("Webhook %s failed: %s", webhook["url"], error_msg)
            if retry_entry is None:
                entry = RetryEntry(webhook, payload, attempt=1)
                with self._lock:
                    self._retry_queue.append(entry)
                logger.info(
                    "Queued %s for retry (attempt 1/%s)",
                    webhook["url"],
                    _MAX_RETRIES,
                )
            elif retry_entry.attempt < _MAX_RETRIES:
                retry_entry.attempt += 1
                retry_entry.next_retry_at = (
                    time.time() + _RETRY_BACKOFF[retry_entry.attempt - 1]
                    if retry_entry.attempt <= len(_RETRY_BACKOFF)
                    else time.time() + 60
                )
                retry_entry.last_error = error_msg
                with self._lock:
                    self._retry_queue.append(retry_entry)
            else:
                logger.error(
                    "Webhook %s permanently failed after %s attempts",
                    webhook["url"],
                    _MAX_RETRIES,
                )
