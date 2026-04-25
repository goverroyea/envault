"""Tests for envault.copy module."""

import pytest
from pathlib import Path
from envault.vault import save_vault, load_vault
from envault.copy import copy_vars, CopyError


PASSPHRASE_A = "passphrase-alpha"
PASSPHRASE_B = "passphrase-beta"


@pytest.fixture
def vault_a(tmp_path):
    path = str(tmp_path / "vault_a.env")
    save_vault(path, PASSPHRASE_A, {"KEY1": "value1", "KEY2": "value2", "SHARED": "from_a"})
    return path


@pytest.fixture
def vault_b(tmp_path):
    path = str(tmp_path / "vault_b.env")
    save_vault(path, PASSPHRASE_B, {"SHARED": "from_b", "EXISTING": "keep_me"})
    return path


def test_copy_all_vars(vault_a, tmp_path):
    dst = str(tmp_path / "vault_dst.env")
    result = copy_vars(vault_a, PASSPHRASE_A, dst, PASSPHRASE_B)
    assert set(result["copied"]) == {"KEY1", "KEY2", "SHARED"}
    assert result["skipped"] == []


def test_copy_creates_destination_if_missing(vault_a, tmp_path):
    dst = str(tmp_path / "new_vault.env")
    assert not Path(dst).exists()
    copy_vars(vault_a, PASSPHRASE_A, dst, PASSPHRASE_B)
    assert Path(dst).exists()


def test_copy_selected_keys(vault_a, tmp_path):
    dst = str(tmp_path / "vault_dst.env")
    result = copy_vars(vault_a, PASSPHRASE_A, dst, PASSPHRASE_B, keys=["KEY1"])
    assert result["copied"] == ["KEY1"]
    data = load_vault(dst, PASSPHRASE_B)
    assert "KEY2" not in data["variables"]


def test_copy_skips_existing_without_overwrite(vault_a, vault_b):
    result = copy_vars(vault_a, PASSPHRASE_A, vault_b, PASSPHRASE_B, keys=["SHARED"])
    assert "SHARED" in result["skipped"]
    data = load_vault(vault_b, PASSPHRASE_B)
    assert data["variables"]["SHARED"] == "from_b"


def test_copy_overwrites_when_flag_set(vault_a, vault_b):
    result = copy_vars(vault_a, PASSPHRASE_A, vault_b, PASSPHRASE_B, keys=["SHARED"], overwrite=True)
    assert "SHARED" in result["copied"]
    data = load_vault(vault_b, PASSPHRASE_B)
    assert data["variables"]["SHARED"] == "from_a"


def test_copy_preserves_existing_keys_in_destination(vault_a, vault_b):
    copy_vars(vault_a, PASSPHRASE_A, vault_b, PASSPHRASE_B, keys=["KEY1"])
    data = load_vault(vault_b, PASSPHRASE_B)
    assert data["variables"]["EXISTING"] == "keep_me"


def test_copy_missing_key_raises(vault_a, tmp_path):
    dst = str(tmp_path / "vault_dst.env")
    with pytest.raises(CopyError, match="Keys not found in source vault"):
        copy_vars(vault_a, PASSPHRASE_A, dst, PASSPHRASE_B, keys=["NONEXISTENT"])


def test_copy_values_are_decryptable_with_dst_passphrase(vault_a, tmp_path):
    dst = str(tmp_path / "vault_dst.env")
    copy_vars(vault_a, PASSPHRASE_A, dst, PASSPHRASE_B, keys=["KEY1"])
    data = load_vault(dst, PASSPHRASE_B)
    assert data["variables"]["KEY1"] == "value1"
