"""Tests for envault.vault module."""

import json
import os
import pytest

from envault.vault import load_vault, save_vault, inject_vault


PASSPHRASE = "test-passphrase-123"
SAMPLE_VARS = {
    "DATABASE_URL": "postgres://localhost/mydb",
    "SECRET_KEY": "supersecretkey",
    "DEBUG": "false",
}


@pytest.fixture
def vault_file(tmp_path):
    """Create a temporary vault file with sample variables."""
    path = str(tmp_path / ".envault")
    save_vault(path, PASSPHRASE, SAMPLE_VARS)
    return path


def test_save_vault_creates_file(tmp_path):
    path = str(tmp_path / ".envault")
    save_vault(path, PASSPHRASE, SAMPLE_VARS)
    assert os.path.exists(path)


def test_save_vault_file_is_not_plaintext(tmp_path):
    path = str(tmp_path / ".envault")
    save_vault(path, PASSPHRASE, SAMPLE_VARS)
    with open(path, "r") as f:
        content = f.read()
    assert "DATABASE_URL" not in content
    assert "supersecretkey" not in content


def test_load_vault_returns_correct_variables(vault_file):
    variables = load_vault(vault_file, PASSPHRASE)
    assert variables == SAMPLE_VARS


def test_load_vault_wrong_passphrase_raises(vault_file):
    with pytest.raises(ValueError):
        load_vault(vault_file, "wrong-passphrase")


def test_load_vault_missing_file_raises(tmp_path):
    path = str(tmp_path / "nonexistent.envault")
    with pytest.raises(FileNotFoundError):
        load_vault(path, PASSPHRASE)


def test_inject_vault_sets_env_vars(vault_file):
    injected = inject_vault(vault_file, PASSPHRASE)
    for key, value in SAMPLE_VARS.items():
        assert os.environ.get(key) == value
    assert injected == SAMPLE_VARS


def test_save_and_load_empty_vault(tmp_path):
    path = str(tmp_path / ".envault")
    save_vault(path, PASSPHRASE, {})
    variables = load_vault(path, PASSPHRASE)
    assert variables == {}


def test_save_vault_overwrites_existing(tmp_path):
    path = str(tmp_path / ".envault")
    save_vault(path, PASSPHRASE, SAMPLE_VARS)
    new_vars = {"NEW_KEY": "new_value"}
    save_vault(path, PASSPHRASE, new_vars)
    variables = load_vault(path, PASSPHRASE)
    assert variables == new_vars
    assert "DATABASE_URL" not in variables
