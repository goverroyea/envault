"""Audit log for tracking vault operations."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

AUDIT_LOG_FILENAME = "audit.log"


def _audit_log_path(vault_path: str) -> Path:
    """Return the audit log path adjacent to the vault file."""
    vault = Path(vault_path)
    return vault.parent / AUDIT_LOG_FILENAME


def record_event(
    vault_path: str,
    action: str,
    key: Optional[str] = None,
    actor: Optional[str] = None,
) -> None:
    """Append a structured audit event to the log file."""
    log_path = _audit_log_path(vault_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "vault": str(Path(vault_path).resolve()),
        "key": key,
        "actor": actor or os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
    }

    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")


def read_events(vault_path: str) -> list[dict]:
    """Read all audit events from the log file."""
    log_path = _audit_log_path(vault_path)
    if not log_path.exists():
        return []

    events = []
    with open(log_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def clear_events(vault_path: str) -> None:
    """Remove the audit log file entirely."""
    log_path = _audit_log_path(vault_path)
    if log_path.exists():
        log_path.unlink()
