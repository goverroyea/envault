"""Tests for the `envault export` CLI command."""

import json
import os

import pytest
from click.testing import CliRunner

from envault.cli import cli
from envault.vault import save_vault


PASSPHRASE = "test-passphrase"
VARIABLES = {"APP_ENV": "production", "PORT": "8080"}


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    path = str(tmp_path / "test.vault")
    save_vault(path, PASSPHRASE, VARIABLES)
    return path


def test_export_default_dotenv(runner, vault_path):
    result = runner.invoke(
        cli, ["export", "--vault", vault_path, "--passphrase", PASSPHRASE]
    )
    assert result.exit_code == 0
    assert "APP_ENV" in result.output
    assert "PORT" in result.output


def test_export_dotenv_format(runner, vault_path):
    result = runner.invoke(
        cli, ["export", "--vault", vault_path, "--passphrase", PASSPHRASE, "--format", "dotenv"]
    )
    assert result.exit_code == 0
    assert 'APP_ENV="production"' in result.output


def test_export_json_format(runner, vault_path):
    result = runner.invoke(
        cli, ["export", "--vault", vault_path, "--passphrase", PASSPHRASE, "--format", "json"]
    )
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["APP_ENV"] == "production"
    assert parsed["PORT"] == "8080"


def test_export_shell_format(runner, vault_path):
    result = runner.invoke(
        cli, ["export", "--vault", vault_path, "--passphrase", PASSPHRASE, "--format", "shell"]
    )
    assert result.exit_code == 0
    assert "APP_ENV='production'" in result.output


def test_export_export_format(runner, vault_path):
    result = runner.invoke(
        cli, ["export", "--vault", vault_path, "--passphrase", PASSPHRASE, "--format", "export"]
    )
    assert result.exit_code == 0
    assert "export APP_ENV='production'" in result.output


def test_export_to_file(runner, vault_path, tmp_path):
    out_file = str(tmp_path / "env_output.env")
    result = runner.invoke(
        cli,
        ["export", "--vault", vault_path, "--passphrase", PASSPHRASE, "--output", out_file],
    )
    assert result.exit_code == 0
    assert os.path.isfile(out_file)
    content = open(out_file).read()
    assert "APP_ENV" in content


def test_export_missing_vault_exits_nonzero(runner, tmp_path):
    result = runner.invoke(
        cli,
        ["export", "--vault", str(tmp_path / "missing.vault"), "--passphrase", PASSPHRASE],
    )
    assert result.exit_code != 0
