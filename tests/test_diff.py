"""Tests for envault.diff and the diff CLI command."""

import json
import pytest
from click.testing import CliRunner

from envault.vault import save_vault
from envault.diff import diff_vaults, VaultDiff
from envault.cli_diff import diff_cmd


PASSPHRASE = "test-pass-diff"


@pytest.fixture()
def vault_file(tmp_path):
    path = str(tmp_path / "test.vault")
    save_vault(path, {"KEY1": "value1", "KEY2": "value2"}, PASSPHRASE)
    return path


def test_diff_identical_snapshot(vault_file):
    snapshot = {"KEY1": "value1", "KEY2": "value2"}
    result = diff_vaults(vault_file, PASSPHRASE, snapshot=snapshot)
    assert not result.has_changes
    assert set(result.unchanged) == {"KEY1", "KEY2"}


def test_diff_added_key(vault_file):
    snapshot = {"KEY1": "value1", "KEY2": "value2", "KEY3": "value3"}
    result = diff_vaults(vault_file, PASSPHRASE, snapshot=snapshot)
    assert "KEY3" in result.added
    assert result.added["KEY3"] == "value3"


def test_diff_removed_key(vault_file):
    snapshot = {"KEY1": "value1"}
    result = diff_vaults(vault_file, PASSPHRASE, snapshot=snapshot)
    assert "KEY2" in result.removed


def test_diff_changed_key(vault_file):
    snapshot = {"KEY1": "new_value", "KEY2": "value2"}
    result = diff_vaults(vault_file, PASSPHRASE, snapshot=snapshot)
    assert "KEY1" in result.changed
    old, new = result.changed["KEY1"]
    assert old == "value1"
    assert new == "new_value"


def test_diff_no_passphrase_b_or_snapshot_raises(vault_file):
    with pytest.raises(ValueError):
        diff_vaults(vault_file, PASSPHRASE)


def test_summary_contains_symbols(vault_file):
    snapshot = {"KEY1": "changed", "KEY3": "added"}
    result = diff_vaults(vault_file, PASSPHRASE, snapshot=snapshot)
    summary = result.summary()
    assert "+" in summary
    assert "-" in summary
    assert "~" in summary


@pytest.fixture()
def runner():
    return CliRunner()


def test_cli_diff_text_output(runner, vault_file, tmp_path):
    second_vault = str(tmp_path / "second.vault")
    save_vault(second_vault, {"KEY1": "value1", "KEY2": "changed"}, "other-pass")

    # We test via snapshot path; use same vault, same passphrase => identical
    result = runner.invoke(
        diff_cmd,
        ["--vault", vault_file, "--passphrase", PASSPHRASE, "--compare-passphrase", PASSPHRASE],
    )
    assert result.exit_code == 0
    assert "identical" in result.output


def test_cli_diff_missing_compare_passphrase_exits(runner, vault_file):
    result = runner.invoke(
        diff_cmd,
        ["--vault", vault_file, "--passphrase", PASSPHRASE],
    )
    assert result.exit_code != 0


def test_cli_diff_json_format(runner, vault_file):
    result = runner.invoke(
        diff_cmd,
        ["--vault", vault_file, "--passphrase", PASSPHRASE,
         "--compare-passphrase", PASSPHRASE, "--format", "json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "has_changes" in data
    assert data["has_changes"] is False
