"""Tests for envault.lock and envault.cli_lock."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.lock import (
    LockError,
    get_lock_info,
    is_locked,
    lock_vault,
    unlock_vault,
)
from envault.cli_lock import lock_group


@pytest.fixture()
def vault_file(tmp_path: Path) -> str:
    p = tmp_path / "test.vault"
    p.write_text("dummy")
    return str(p)


# --- Unit tests for lock.py ---

def test_lock_creates_lock_file(vault_file):
    lock_vault(vault_file)
    assert Path(vault_file).with_suffix(".lock").exists()


def test_lock_returns_record(vault_file):
    record = lock_vault(vault_file, reason="ci", locked_by="alice")
    assert record["locked_by"] == "alice"
    assert record["reason"] == "ci"
    assert "locked_at" in record


def test_lock_twice_raises(vault_file):
    lock_vault(vault_file)
    with pytest.raises(LockError, match="already locked"):
        lock_vault(vault_file)


def test_is_locked_false_before_lock(vault_file):
    assert is_locked(vault_file) is False


def test_is_locked_true_after_lock(vault_file):
    lock_vault(vault_file)
    assert is_locked(vault_file) is True


def test_unlock_removes_lock_file(vault_file):
    lock_vault(vault_file)
    unlock_vault(vault_file)
    assert not Path(vault_file).with_suffix(".lock").exists()


def test_unlock_when_not_locked_raises(vault_file):
    with pytest.raises(LockError, match="not locked"):
        unlock_vault(vault_file)


def test_get_lock_info_returns_none_when_unlocked(vault_file):
    assert get_lock_info(vault_file) is None


def test_get_lock_info_returns_dict_when_locked(vault_file):
    lock_vault(vault_file, reason="deploy", locked_by="bob")
    info = get_lock_info(vault_file)
    assert info is not None
    assert info["locked_by"] == "bob"
    assert info["reason"] == "deploy"


# --- CLI tests for cli_lock.py ---

@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_lock_set(runner, vault_file):
    result = runner.invoke(lock_group, ["set", "--vault", vault_file, "--by", "ci"])
    assert result.exit_code == 0
    assert "locked" in result.output.lower()


def test_cli_lock_unset(runner, vault_file):
    lock_vault(vault_file)
    result = runner.invoke(lock_group, ["unset", "--vault", vault_file])
    assert result.exit_code == 0
    assert "unlocked" in result.output.lower()


def test_cli_status_not_locked(runner, vault_file):
    result = runner.invoke(lock_group, ["status", "--vault", vault_file])
    assert result.exit_code == 0
    assert "not locked" in result.output.lower()


def test_cli_status_locked_json(runner, vault_file):
    lock_vault(vault_file, reason="freeze", locked_by="ops")
    result = runner.invoke(lock_group, ["status", "--vault", vault_file, "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["locked"] is True
    assert data["locked_by"] == "ops"
    assert data["reason"] == "freeze"
