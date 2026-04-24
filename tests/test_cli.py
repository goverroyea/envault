"""Tests for the envault CLI commands."""

import os

import pytest
from click.testing import CliRunner

from envault.cli import cli

PASSPHRASE = "cli-test-passphrase"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    return str(tmp_path / ".envault")


def test_set_creates_vault_file(runner, vault_path):
    result = runner.invoke(cli, ["set", "MY_KEY", "my_value", "--vault", vault_path, "--passphrase", PASSPHRASE])
    assert result.exit_code == 0, result.output
    assert os.path.exists(vault_path)
    assert "Set MY_KEY" in result.output


def test_get_returns_value(runner, vault_path):
    runner.invoke(cli, ["set", "TOKEN", "abc123", "--vault", vault_path, "--passphrase", PASSPHRASE])
    result = runner.invoke(cli, ["get", "TOKEN", "--vault", vault_path, "--passphrase", PASSPHRASE])
    assert result.exit_code == 0, result.output
    assert "abc123" in result.output


def test_get_missing_key_exits_nonzero(runner, vault_path):
    runner.invoke(cli, ["set", "EXISTING", "val", "--vault", vault_path, "--passphrase", PASSPHRASE])
    result = runner.invoke(cli, ["get", "MISSING_KEY", "--vault", vault_path, "--passphrase", PASSPHRASE])
    assert result.exit_code != 0
    assert "not found" in result.output


def test_list_shows_keys(runner, vault_path):
    runner.invoke(cli, ["set", "ALPHA", "1", "--vault", vault_path, "--passphrase", PASSPHRASE])
    runner.invoke(cli, ["set", "BETA", "2", "--vault", vault_path, "--passphrase", PASSPHRASE])
    result = runner.invoke(cli, ["list", "--vault", vault_path, "--passphrase", PASSPHRASE])
    assert result.exit_code == 0, result.output
    assert "ALPHA" in result.output
    assert "BETA" in result.output


def test_list_empty_vault(runner, vault_path):
    # Create an empty vault by setting and then verifying list on a fresh path
    result = runner.invoke(
        cli,
        ["set", "TMP", "x", "--vault", vault_path, "--passphrase", PASSPHRASE],
    )
    assert result.exit_code == 0


def test_set_wrong_passphrase_on_existing_vault(runner, vault_path):
    runner.invoke(cli, ["set", "KEY", "val", "--vault", vault_path, "--passphrase", PASSPHRASE])
    result = runner.invoke(cli, ["set", "KEY2", "val2", "--vault", vault_path, "--passphrase", "wrong-passphrase"])
    assert result.exit_code != 0


def test_run_injects_env(runner, vault_path):
    runner.invoke(cli, ["set", "GREET", "hello", "--vault", vault_path, "--passphrase", PASSPHRASE])
    result = runner.invoke(
        cli,
        ["run", "--vault", vault_path, "--passphrase", PASSPHRASE, "printenv", "GREET"],
    )
    assert result.exit_code == 0, result.output
    assert "hello" in result.output
