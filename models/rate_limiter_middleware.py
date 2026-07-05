"""Sliding-window rate limiter for outbound webhook calls.

Tracks request frequency per endpoint using an in-memory sliding window
and optionally persists counters to disk so limits survive restarts.
"""

from __future__ import annotations

import json
import threading
import time
from collections import defaultdict
from pathlib import Path


class RateLimiter:
    """Token-bucket-style rate limiter backed by a sliding window.

    Usage::

        limiter = RateLimiter(max_requests=10, window_seconds=60)
        if limiter.allow("https://hooks.example.com/alert"):
            send_webhook(...)
        else:
            logger.warning("Rate limited, skipping webhook")
    """

    def __init__(
        self,
        max_requests: int = 30,
        window_seconds: int = 60,
        persist_path: str | None = None,
    ):
        self._max = max_requests
        self._window = window_seconds
        self._persist_path = Path(persist_path) if persist_path else None
        self._lock = threading.Lock()
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._load()

    def allow(self, key: str) -> bool:
        """Check if *key* is allowed under the rate limit.

        Returns ``True`` if the request should proceed, ``False`` if
        the limit has been exceeded for the current window.
        """
        now = time.time()
        cutoff = now - self._window
        with self._lock:
            window = self._buckets[key]
            window[:] = [t for t in window if t > cutoff]
            if len(window) >= self._max:
                return False
            window.append(now)
            self._dirty = True
            return True

    def remaining(self, key: str) -> int:
        """Return how many requests *key* can still make in this window."""
        now = time.time()
        cutoff = now - self._window
        with self._lock:
            window = self._buckets[key]
            window[:] = [t for t in window if t > cutoff]
            return max(0, self._max - len(window))

    def reset(self, key: str | None = None) -> None:
        """Clear counters for *key*, or all keys when *key* is ``None``."""
        with self._lock:
            if key:
                self._buckets.pop(key, None)
            else:
                self._buckets.clear()
            self._dirty = True

    # ------------------------------------------------------------------
    # Optional disk persistence
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self._persist_path or not self._persist_path.exists():
            return
        try:
            raw = self._persist_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            self._buckets = defaultdict(
                list, {k: v for k, v in data.items() if isinstance(v, list)}
            )
        except (json.JSONDecodeError, OSError):
            pass

    def persist(self) -> None:
        """Write current state to disk (useful for graceful shutdown)."""
        if not self._persist_path:
            return
        with self._lock:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            self._persist_path.write_text(
                json.dumps(self._buckets, indent=2, default=list),
                encoding="utf-8",
            )
            self._dirty = False

    def __del__(self):
        if getattr(self, "_dirty", False):
            self.persist()
