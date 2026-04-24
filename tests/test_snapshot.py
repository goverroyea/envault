"""Tests for envault.snapshot."""

from __future__ import annotations

import json
import pytest

from envault.snapshot import (
    SnapshotError,
    _snapshots_dir,
    create_snapshot,
    list_snapshots,
    restore_snapshot,
)
from envault.vault import save_vault, load_vault


PASSPHRASE = "test-secret-passphrase"
VARIABLES = {"API_KEY": "abc123", "DB_URL": "postgres://localhost/dev"}


@pytest.fixture
def vault_file(tmp_path):
    path = str(tmp_path / "test.vault")
    save_vault(path, PASSPHRASE, VARIABLES)
    return path


def test_create_snapshot_returns_id(vault_file):
    snap_id = create_snapshot(vault_file, PASSPHRASE)
    assert isinstance(snap_id, str)
    assert len(snap_id) > 0


def test_create_snapshot_with_label(vault_file):
    snap_id = create_snapshot(vault_file, PASSPHRASE, label="before-migration")
    assert "before-migration" in snap_id


def test_create_snapshot_writes_file(vault_file):
    snap_id = create_snapshot(vault_file, PASSPHRASE)
    snap_dir = _snapshots_dir(vault_file)
    assert (snap_dir / f"{snap_id}.json").exists()


def test_create_snapshot_stores_variables(vault_file):
    snap_id = create_snapshot(vault_file, PASSPHRASE)
    snap_dir = _snapshots_dir(vault_file)
    data = json.loads((snap_dir / f"{snap_id}.json").read_text())
    assert data["variables"] == VARIABLES


def test_create_snapshot_wrong_passphrase_raises(vault_file):
    with pytest.raises(Exception):
        create_snapshot(vault_file, "wrong-passphrase")


def test_list_snapshots_empty_when_none(vault_file):
    result = list_snapshots(vault_file)
    assert result == []


def test_list_snapshots_returns_metadata(vault_file):
    create_snapshot(vault_file, PASSPHRASE, label="snap1")
    snapshots = list_snapshots(vault_file)
    assert len(snapshots) == 1
    snap = snapshots[0]
    assert "snapshot_id" in snap
    assert snap["variable_count"] == len(VARIABLES)
    assert snap["label"] == "snap1"


def test_list_snapshots_newest_first(vault_file):
    id1 = create_snapshot(vault_file, PASSPHRASE, label="first")
    id2 = create_snapshot(vault_file, PASSPHRASE, label="second")
    snapshots = list_snapshots(vault_file)
    ids = [s["snapshot_id"] for s in snapshots]
    assert ids.index(id2) < ids.index(id1)


def test_restore_snapshot_returns_count(vault_file):
    snap_id = create_snapshot(vault_file, PASSPHRASE)
    count = restore_snapshot(vault_file, PASSPHRASE, snap_id)
    assert count == len(VARIABLES)


def test_restore_snapshot_overwrites_vault(vault_file):
    snap_id = create_snapshot(vault_file, PASSPHRASE)
    save_vault(vault_file, PASSPHRASE, {"NEW_VAR": "new_value"})
    restore_snapshot(vault_file, PASSPHRASE, snap_id)
    restored = load_vault(vault_file, PASSPHRASE)
    assert restored == VARIABLES


def test_restore_snapshot_missing_raises(vault_file):
    with pytest.raises(SnapshotError, match="not found"):
        restore_snapshot(vault_file, PASSPHRASE, "nonexistent_snapshot")
