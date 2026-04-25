"""Tests for envault.merge."""

import pytest

from envault.vault import save_vault
from envault.merge import MergeError, MergeResult, merge_vaults


@pytest.fixture
def vault_a(tmp_path):
    path = str(tmp_path / "a.vault")
    save_vault(path, "pass-a", {"FOO": "foo_val", "BAR": "bar_val", "SHARED": "from_a"})
    return path


@pytest.fixture
def vault_b(tmp_path):
    path = str(tmp_path / "b.vault")
    save_vault(path, "pass-b", {"SHARED": "from_b", "BAZ": "baz_val"})
    return path


def test_merge_adds_new_keys(vault_a, tmp_path):
    dst = str(tmp_path / "dst.vault")
    result = merge_vaults(vault_a, "pass-a", dst, "pass-dst")
    assert "FOO" in result.added
    assert "BAR" in result.added
    assert "SHARED" in result.added
    assert result.total_changes == 3


def test_merge_skips_existing_keys_by_default(vault_a, vault_b):
    result = merge_vaults(vault_a, "pass-a", vault_b, "pass-b")
    assert "SHARED" in result.skipped
    assert "FOO" in result.added
    assert "BAR" in result.added


def test_merge_overwrites_when_flag_set(vault_a, vault_b):
    result = merge_vaults(vault_a, "pass-a", vault_b, "pass-b", overwrite=True)
    assert "SHARED" in result.overwritten
    assert result.skipped == []


def test_merge_selected_keys_only(vault_a, tmp_path):
    dst = str(tmp_path / "dst.vault")
    result = merge_vaults(vault_a, "pass-a", dst, "pass-dst", keys=["FOO"])
    assert result.added == ["FOO"]
    assert "BAR" not in result.added


def test_merge_missing_key_raises(vault_a, tmp_path):
    dst = str(tmp_path / "dst.vault")
    with pytest.raises(MergeError, match="NOPE"):
        merge_vaults(vault_a, "pass-a", dst, "pass-dst", keys=["NOPE"])


def test_merge_dry_run_does_not_write(vault_a, tmp_path):
    dst = str(tmp_path / "dst.vault")
    merge_vaults(vault_a, "pass-a", dst, "pass-dst", dry_run=True)
    assert not (tmp_path / "dst.vault").exists()


def test_merge_result_total_changes(vault_a, vault_b):
    result = merge_vaults(vault_a, "pass-a", vault_b, "pass-b", overwrite=True)
    assert result.total_changes == len(result.added) + len(result.overwritten)


def test_merge_creates_destination_if_missing(vault_a, tmp_path):
    dst = str(tmp_path / "new.vault")
    merge_vaults(vault_a, "pass-a", dst, "new-pass")
    assert (tmp_path / "new.vault").exists()
