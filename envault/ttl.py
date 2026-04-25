"""TTL (time-to-live) support for vault variables."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

TTL_META_KEY = "__ttl__"


class TTLError(Exception):
    """Raised when a TTL operation fails."""


def set_ttl(vault: dict, key: str, seconds: int) -> dict:
    """Attach a TTL (expiry timestamp) to *key* in the vault.

    Returns a new vault dict with updated metadata; does not mutate *vault*.
    Raises TTLError if *key* is not present in the vault variables.
    """
    variables = vault.get("variables", {})
    if key not in variables:
        raise TTLError(f"Key {key!r} not found in vault.")
    if seconds <= 0:
        raise TTLError("TTL must be a positive number of seconds.")

    meta = dict(vault.get("meta", {}))
    ttl_map: Dict[str, float] = dict(meta.get(TTL_META_KEY, {}))
    ttl_map[key] = time.time() + seconds
    meta[TTL_META_KEY] = ttl_map
    return {**vault, "meta": meta}


def get_ttl(vault: dict, key: str) -> Optional[float]:
    """Return the expiry timestamp for *key*, or None if no TTL is set."""
    ttl_map: Dict[str, float] = vault.get("meta", {}).get(TTL_META_KEY, {})
    return ttl_map.get(key)


def is_expired(vault: dict, key: str) -> bool:
    """Return True if *key* has a TTL that has already passed."""
    expiry = get_ttl(vault, key)
    if expiry is None:
        return False
    return time.time() >= expiry


def remove_ttl(vault: dict, key: str) -> dict:
    """Remove the TTL for *key*.  Returns a new vault dict."""
    meta = dict(vault.get("meta", {}))
    ttl_map: Dict[str, float] = dict(meta.get(TTL_META_KEY, {}))
    ttl_map.pop(key, None)
    meta[TTL_META_KEY] = ttl_map
    return {**vault, "meta": meta}


def purge_expired(vault: dict) -> tuple[dict, List[str]]:
    """Remove all expired variables from the vault.

    Returns ``(new_vault, removed_keys)``.
    """
    variables = dict(vault.get("variables", {}))
    removed: List[str] = []
    for key in list(variables):
        if is_expired(vault, key):
            del variables[key]
            removed.append(key)
    new_vault = {**vault, "variables": variables}
    for key in removed:
        new_vault = remove_ttl(new_vault, key)
    return new_vault, removed
