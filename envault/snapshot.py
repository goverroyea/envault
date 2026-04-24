"""Snapshot management for envault vaults."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import load_vault, save_vault


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def _snapshots_dir(vault_path: str) -> Path:
    """Return the directory used to store snapshots for a given vault."""
    vault = Path(vault_path)
    return vault.parent / ".envault_snapshots" / vault.stem


def create_snapshot(
    vault_path: str,
    passphrase: str,
    label: Optional[str] = None,
) -> str:
    """Persist a named snapshot of the current vault contents.

    Returns the snapshot id (timestamp-based filename stem).
    """
    variables: Dict[str, str] = load_vault(vault_path, passphrase)

    snap_dir = _snapshots_dir(vault_path)
    snap_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_id = f"{ts}_{label}" if label else ts
    snap_path = snap_dir / f"{snapshot_id}.json"

    if snap_path.exists():
        raise SnapshotError(f"Snapshot '{snapshot_id}' already exists.")

    meta = {
        "snapshot_id": snapshot_id,
        "vault_path": str(vault_path),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "label": label,
        "variables": variables,
    }
    snap_path.write_text(json.dumps(meta, indent=2))
    return snapshot_id


def list_snapshots(vault_path: str) -> List[dict]:
    """Return metadata for all snapshots of *vault_path*, newest first."""
    snap_dir = _snapshots_dir(vault_path)
    if not snap_dir.exists():
        return []

    snapshots = []
    for p in sorted(snap_dir.glob("*.json"), reverse=True):
        data = json.loads(p.read_text())
        snapshots.append(
            {
                "snapshot_id": data["snapshot_id"],
                "created_at": data["created_at"],
                "label": data.get("label"),
                "variable_count": len(data.get("variables", {})),
            }
        )
    return snapshots


def restore_snapshot(
    vault_path: str,
    passphrase: str,
    snapshot_id: str,
) -> int:
    """Overwrite the vault with variables from *snapshot_id*.

    Returns the number of variables restored.
    """
    snap_dir = _snapshots_dir(vault_path)
    snap_path = snap_dir / f"{snapshot_id}.json"

    if not snap_path.exists():
        raise SnapshotError(f"Snapshot '{snapshot_id}' not found.")

    data = json.loads(snap_path.read_text())
    variables: Dict[str, str] = data["variables"]
    save_vault(vault_path, passphrase, variables)
    return len(variables)
