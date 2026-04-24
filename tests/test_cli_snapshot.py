import pytest
from click.testing import CliRunner
from pathlib import Path
from envault.cli_snapshot import snapshot_group
from envault.vault import save_vault, load_vault


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_path(tmp_path):
    path = tmp_path / "test.vault"
    save_vault(path, "secret", {"FOO": "bar", "BAZ": "qux"})
    return path


def test_create_snapshot_prints_id(runner, vault_path):
    result = runner.invoke(
        snapshot_group,
        ["create", "--vault", str(vault_path), "--passphrase", "secret"],
    )
    assert result.exit_code == 0
    assert "Snapshot created:" in result.output


def test_create_snapshot_with_label(runner, vault_path):
    result = runner.invoke(
        snapshot_group,
        ["create", "--vault", str(vault_path), "--passphrase", "secret", "--label", "before-deploy"],
    )
    assert result.exit_code == 0
    assert "Snapshot created:" in result.output


def test_list_snapshots_empty(runner, tmp_path):
    vault_path = tmp_path / "empty.vault"
    save_vault(vault_path, "secret", {"X": "1"})
    result = runner.invoke(
        snapshot_group,
        ["list", "--vault", str(vault_path)],
    )
    assert result.exit_code == 0
    assert "No snapshots found." in result.output


def test_list_snapshots_shows_entry(runner, vault_path):
    runner.invoke(
        snapshot_group,
        ["create", "--vault", str(vault_path), "--passphrase", "secret", "--label", "v1"],
    )
    result = runner.invoke(
        snapshot_group,
        ["list", "--vault", str(vault_path)],
    )
    assert result.exit_code == 0
    assert "v1" in result.output
    assert "2 vars" in result.output


def test_list_snapshots_json_output(runner, vault_path):
    import json
    runner.invoke(
        snapshot_group,
        ["create", "--vault", str(vault_path), "--passphrase", "secret"],
    )
    result = runner.invoke(
        snapshot_group,
        ["list", "--vault", str(vault_path), "--json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 1


def test_restore_snapshot_overwrites_vault(runner, vault_path):
    runner.invoke(
        snapshot_group,
        ["create", "--vault", str(vault_path), "--passphrase", "secret"],
    )
    # Overwrite vault with different data
    save_vault(vault_path, "secret", {"NEW": "value"})
    # Get snapshot id
    from envault.snapshot import list_snapshots
    snapshots = list_snapshots(vault_path)
    snap_id = snapshots[0]["id"]

    result = runner.invoke(
        snapshot_group,
        ["restore", snap_id, "--vault", str(vault_path), "--passphrase", "secret", "--confirm"],
    )
    assert result.exit_code == 0
    assert "Restored" in result.output
    restored = load_vault(vault_path, "secret")
    assert restored.get("FOO") == "bar"


def test_restore_nonexistent_snapshot_exits_nonzero(runner, vault_path):
    result = runner.invoke(
        snapshot_group,
        ["restore", "nonexistent-id", "--vault", str(vault_path), "--passphrase", "secret", "--confirm"],
    )
    assert result.exit_code != 0
