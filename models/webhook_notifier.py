"""Webhook notification system for real-time SMS threat alerts.

Sends HTTP POST notifications to configured webhook URLs whenever
a message is classified as SPAM, enabling external integrations
(Slack, Discord, custom APIs, etc.).
"""

import json
import logging
import os
import threading
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any

import requests as req

from models.rate_limiter_middleware import RateLimiter

logger = logging.getLogger(__name__)


class WebhookNotifier:
    """Manages webhook endpoints and sends alerts asynchronously."""

    def __init__(self, config_path: str | None = None, rate_limiter: RateLimiter | None = None):
        if config_path is None:
            config_path = os.getenv(
                "SPAMLYSER_WEBHOOK_CONFIG",
                str(Path(__file__).resolve().parent.parent / "data" / "webhooks.json"),
            )
        self._config_path = Path(config_path)
        self._webhooks: list[dict[str, Any]] = []
        self._rate_limiter = rate_limiter or RateLimiter(
            max_requests=int(os.getenv("SPAMLYSER_RATE_LIMIT_MAX", "30")),
            window_seconds=int(os.getenv("SPAMLYSER_RATE_LIMIT_WINDOW", "60")),
            persist_path=os.getenv(
                "SPAMLYSER_RATE_LIMIT_DB",
                str(Path(__file__).resolve().parent.parent / "data" / "rate_limiter_state.json"),
            ),
        )
        self._load_config()

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
                    args=(wh, payload),
                    daemon=True,
                ).start()

    def _send_single(self, webhook: dict, payload: dict):
        url = webhook["url"]
        if not self._rate_limiter.allow(url):
            logger.warning("Rate limit exceeded for %s, skipping notification", url)
            return
        try:
            headers = {"Content-Type": "application/json"}
            if webhook.get("secret"):
                headers["X-Webhook-Secret"] = webhook["secret"]
            resp = req.post(
                url,
                json=payload,
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
        except req.RequestException as e:
            logger.warning("Webhook %s failed: %s", url, e)

    def get_rate_limiter(self) -> RateLimiter:
        return self._rate_limiter
