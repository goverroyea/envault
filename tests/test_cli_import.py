"""Tests for envault/cli_import.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_import import import_cmd
from envault.vault import load_vault, save_vault


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    return tmp_path / "test.vault"


def test_import_dotenv_file(runner, vault_path, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nBAZ=qux\n")
    result = runner.invoke(
        import_cmd,
        [str(env_file), "--vault", str(vault_path), "--passphrase", "secret"],
    )
    assert result.exit_code == 0
    assert "Imported 2" in result.output
    data = load_vault(vault_path, "secret")
    assert data["FOO"] == "bar"
    assert data["BAZ"] == "qux"


def test_import_json_file(runner, vault_path, tmp_path):
    json_file = tmp_path / "vars.json"
    json_file.write_text(json.dumps({"TOKEN": "abc", "PORT": "8080"}))
    result = runner.invoke(
        import_cmd,
        [str(json_file), "--vault", str(vault_path), "--passphrase", "secret"],
    )
    assert result.exit_code == 0
    data = load_vault(vault_path, "secret")
    assert data["TOKEN"] == "abc"


def test_import_no_overwrite_by_default(runner, vault_path, tmp_path):
    save_vault(vault_path, "secret", {"FOO": "original"})
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=new\nBAR=added\n")
    result = runner.invoke(
        import_cmd,
        [str(env_file), "--vault", str(vault_path), "--passphrase", "secret"],
    )
    assert result.exit_code == 0
    assert "Skipped 1" in result.output
    data = load_vault(vault_path, "secret")
    assert data["FOO"] == "original"
    assert data["BAR"] == "added"


def test_import_overwrite_flag(runner, vault_path, tmp_path):
    save_vault(vault_path, "secret", {"FOO": "original"})
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=updated\n")
    result = runner.invoke(
        import_cmd,
        [str(env_file), "--overwrite", "--vault", str(vault_path), "--passphrase", "secret"],
    )
    assert result.exit_code == 0
    data = load_vault(vault_path, "secret")
    assert data["FOO"] == "updated"


def test_import_dry_run_does_not_write(runner, vault_path, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DRY=run\n")
    result = runner.invoke(
        import_cmd,
        [str(env_file), "--dry-run", "--vault", str(vault_path), "--passphrase", "secret"],
    )
    assert result.exit_code == 0
    assert "dry-run" in result.output
    assert not vault_path.exists()


def test_import_shell_format(runner, vault_path, tmp_path):
    sh_file = tmp_path / "vars.sh"
    sh_file.write_text('export API_KEY="mykey"\nexport DEBUG=true\n')
    result = runner.invoke(
        import_cmd,
        [str(sh_file), "--format", "shell", "--vault", str(vault_path), "--passphrase", "s"],
    )
    assert result.exit_code == 0
    data = load_vault(vault_path, "s")
    assert data["API_KEY"] == "mykey"
    assert data["DEBUG"] == "true"
