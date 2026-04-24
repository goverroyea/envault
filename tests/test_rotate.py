"""Tests for envault.rotate and the rotate CLI command."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.vault import save_vault, load_vault
from envault.rotate import rotate_passphrase, RotationError
from envault.cli_rotate import rotate_cmd


VARS = {"DB_URL": "postgres://localhost/test", "SECRET": "s3cr3t"}
OLD_PASS = "old-passphrase"
NEW_PASS = "new-passphrase"


@pytest.fixture()
def vault_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.vault"
    save_vault(path, VARS, OLD_PASS)
    return path


def test_rotate_returns_variable_count(vault_file: Path) -> None:
    count = rotate_passphrase(vault_file, OLD_PASS, NEW_PASS)
    assert count == len(VARS)


def test_rotate_new_passphrase_decrypts(vault_file: Path) -> None:
    rotate_passphrase(vault_file, OLD_PASS, NEW_PASS)
    result = load_vault(vault_file, NEW_PASS)
    assert result == VARS


def test_rotate_old_passphrase_no_longer_works(vault_file: Path) -> None:
    rotate_passphrase(vault_file, OLD_PASS, NEW_PASS)
    with pytest.raises(Exception):
        load_vault(vault_file, OLD_PASS)


def test_rotate_same_passphrase_raises(vault_file: Path) -> None:
    with pytest.raises(ValueError, match="differ"):
        rotate_passphrase(vault_file, OLD_PASS, OLD_PASS)


def test_rotate_wrong_old_passphrase_raises(vault_file: Path) -> None:
    with pytest.raises(RotationError):
        rotate_passphrase(vault_file, "wrong", NEW_PASS)


def test_rotate_missing_vault_raises(tmp_path: Path) -> None:
    with pytest.raises(RotationError, match="not found"):
        rotate_passphrase(tmp_path / "missing.vault", OLD_PASS, NEW_PASS)


# --- CLI tests ---


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_rotate_success(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(
        rotate_cmd,
        ["--vault", str(vault_file), "--passphrase", OLD_PASS, "--new-passphrase", NEW_PASS],
    )
    assert result.exit_code == 0
    assert "re-encrypted" in result.output


def test_cli_rotate_wrong_passphrase_exits_nonzero(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(
        rotate_cmd,
        ["--vault", str(vault_file), "--passphrase", "bad", "--new-passphrase", NEW_PASS],
    )
    assert result.exit_code != 0


def test_cli_rotate_same_passphrase_exits_nonzero(runner: CliRunner, vault_file: Path) -> None:
    result = runner.invoke(
        rotate_cmd,
        ["--vault", str(vault_file), "--passphrase", OLD_PASS, "--new-passphrase", OLD_PASS],
    )
    assert result.exit_code != 0
