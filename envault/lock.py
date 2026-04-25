"""Vault locking: temporarily lock a vault to prevent reads/writes."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class LockError(Exception):
    """Raised when a vault lock operation fails."""


def _lock_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".lock")


def lock_vault(
    vault_path: str,
    reason: str = "",
    locked_by: Optional[str] = None,
) -> dict:
    """Create a lock file for the given vault.

    Returns the lock record that was written.
    Raises LockError if the vault is already locked.
    """
    lp = _lock_path(vault_path)
    if lp.exists():
        existing = json.loads(lp.read_text())
        raise LockError(
            f"Vault is already locked (by '{existing.get('locked_by', 'unknown')}' "
            f"at {existing.get('locked_at', '?')})"
        )

    record = {
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "locked_by": locked_by or os.environ.get("USER", "unknown"),
        "reason": reason,
        "vault": str(vault_path),
    }
    lp.write_text(json.dumps(record, indent=2))
    return record


def unlock_vault(vault_path: str) -> None:
    """Remove the lock file for the given vault.

    Raises LockError if the vault is not locked.
    """
    lp = _lock_path(vault_path)
    if not lp.exists():
        raise LockError("Vault is not locked.")
    lp.unlink()


def get_lock_info(vault_path: str) -> Optional[dict]:
    """Return lock metadata if the vault is locked, else None."""
    lp = _lock_path(vault_path)
    if not lp.exists():
        return None
    return json.loads(lp.read_text())


def is_locked(vault_path: str) -> bool:
    """Return True if the vault has an active lock file."""
    return _lock_path(vault_path).exists()
