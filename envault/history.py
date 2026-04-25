"""Track per-key change history within a vault."""

from __future__ import annotations

import datetime
from typing import Any

from envault.vault import load_vault, save_vault

HISTORY_META_KEY = "__history__"
MAX_HISTORY = 20


class HistoryError(Exception):
    pass


def _now_iso() -> str:
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def record_change(
    vault: dict[str, Any], key: str, old_value: str | None, new_value: str | None
) -> dict[str, Any]:
    """Return a new vault dict with a history entry appended for *key*."""
    meta = vault.get("__meta__", {})
    history: dict[str, list] = dict(meta.get(HISTORY_META_KEY, {}))

    entry = {
        "ts": _now_iso(),
        "old": old_value,
        "new": new_value,
    }

    key_log: list = list(history.get(key, []))
    key_log.append(entry)
    if len(key_log) > MAX_HISTORY:
        key_log = key_log[-MAX_HISTORY:]

    history[key] = key_log
    new_meta = {**meta, HISTORY_META_KEY: history}
    return {**vault, "__meta__": new_meta}


def get_history(vault: dict[str, Any], key: str) -> list[dict]:
    """Return the change log for *key*, oldest first."""
    meta = vault.get("__meta__", {})
    history = meta.get(HISTORY_META_KEY, {})
    return list(history.get(key, []))


def clear_history(vault: dict[str, Any], key: str | None = None) -> dict[str, Any]:
    """Clear history for a specific key or for all keys if *key* is None."""
    meta = vault.get("__meta__", {})
    history: dict = dict(meta.get(HISTORY_META_KEY, {}))

    if key is None:
        history = {}
    else:
        history.pop(key, None)

    new_meta = {**meta, HISTORY_META_KEY: history}
    return {**vault, "__meta__": new_meta}
