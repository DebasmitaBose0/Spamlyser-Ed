"""Session state persistence — saves and restores user preferences across page reloads."""

import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from config import SESSION_PERSIST_PATH

_SAVE_INTERVAL = timedelta(seconds=10)
_last_save: dict[str, datetime] = {}
_lock = threading.Lock()

PERSISTENT_KEYS = {
    "settings", "current_page", "theme", "language_preference"
}

TRANSIENT_DEFAULTS = {
    "settings": {
        "default_model": "DistilBERT",
        "confidence_threshold": 0.7,
        "enable_detailed_analysis": True,
        "auto_preprocess": True,
        "theme": "Light",
        "show_confidence_scores": True,
        "enable_batch_mode": False,
        "max_message_length": 500,
        "cache_models": True,
        "gpu_acceleration": False,
    },
    "current_page": "home",
}


def save_session_state(state: dict[str, Any], session_id: str | None = None) -> bool:
    """Persist selected keys from *state* to the session file.

    Only keys listed in *PERSISTENT_KEYS* are saved (plus any extras in
    ``state["_extra_persist_keys"]``).
    """
    sid = session_id or "default"
    now = datetime.now()
    last = _last_save.get(sid)

    if last and (now - last) < _SAVE_INTERVAL:
        return False

    persist_keys = set(PERSISTENT_KEYS)
    persist_keys.update(state.get("_extra_persist_keys", set()))

    payload: dict[str, Any] = {"__meta__": {"saved_at": now.isoformat(), "session_id": sid}}
    for key in persist_keys:
        if key in state and key != "_extra_persist_keys":
            val = state[key]
            try:
                json.dumps(val)
                payload[key] = val
            except (TypeError, ValueError):
                pass

    path = Path(SESSION_PERSIST_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _lock:
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        _last_save[sid] = now
        return True
    except (OSError, json.JSONEncodeError) as exc:
        import logging
        logging.getLogger(__name__).warning("Failed to persist session: %s", exc)
        return False


def restore_session_state(session_id: str | None = None) -> dict[str, Any]:
    """Load previously persisted session data from disk.

    Returns a dict with the stored keys merged over ``TRANSIENT_DEFAULTS`` so
    callers can safely apply it with ``st.session_state.update(...)``.
    """
    sid = session_id or "default"
    result = dict(TRANSIENT_DEFAULTS)

    path = Path(SESSION_PERSIST_PATH)
    if not path.exists():
        return result

    try:
        with _lock:
            payload: dict = json.loads(path.read_text(encoding="utf-8"))
        meta = payload.pop("__meta__", {})
        if meta.get("session_id") != sid:
            return result
        for key, val in payload.items():
            if key in PERSISTENT_KEYS or key.startswith("_"):
                result[key] = val
    except (OSError, json.JSONDecodeError) as exc:
        import logging
        logging.getLogger(__name__).warning("Failed to restore session: %s", exc)

    return result


def clear_persisted_session(session_id: str | None = None) -> None:
    """Delete the persisted session file."""
    sid = session_id or "default"
    path = Path(SESSION_PERSIST_PATH)
    if path.exists():
        try:
            with _lock:
                payload: dict = json.loads(path.read_text(encoding="utf-8"))
                meta = payload.get("__meta__", {})
                if meta.get("session_id") != sid:
                    return
                path.unlink()
            _last_save.pop(sid, None)
        except (OSError, json.JSONDecodeError):
            pass
