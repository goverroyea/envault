"""Tests for envault.config helpers."""

import json
import os

import pytest

from envault.config import (
    CONFIG_FILENAME,
    load_config,
    resolve_passphrase,
    resolve_vault_path,
    save_config,
)


@pytest.fixture()
def config_dir(tmp_path):
    return str(tmp_path)


def test_load_config_defaults_when_no_file(config_dir):
    config = load_config(config_dir)
    assert config["vault_path"] == ".envault"
    assert config["passphrase_env"] == "ENVAULT_PASSPHRASE"


def test_save_and_load_config_round_trip(config_dir):
    data = {"vault_path": "custom.vault", "passphrase_env": "MY_PASS"}
    save_config(data, config_dir)
    loaded = load_config(config_dir)
    assert loaded["vault_path"] == "custom.vault"
    assert loaded["passphrase_env"] == "MY_PASS"


def test_save_config_creates_json_file(config_dir):
    save_config({"vault_path": "x.vault"}, config_dir)
    config_file = os.path.join(config_dir, CONFIG_FILENAME)
    assert os.path.exists(config_file)
    with open(config_file) as fh:
        raw = json.load(fh)
    assert raw["vault_path"] == "x.vault"


def test_load_config_merges_with_defaults(config_dir):
    save_config({"vault_path": "override.vault"}, config_dir)
    config = load_config(config_dir)
    # default key still present
    assert "passphrase_env" in config
    assert config["vault_path"] == "override.vault"


def test_load_config_raises_on_invalid_json(config_dir):
    config_file = os.path.join(config_dir, CONFIG_FILENAME)
    with open(config_file, "w") as fh:
        fh.write("not-json{{{")
    with pytest.raises(ValueError, match="Failed to read config"):
        load_config(config_dir)


def test_resolve_vault_path_uses_config(config_dir):
    save_config({"vault_path": "my.vault"}, config_dir)
    assert resolve_vault_path(config_dir) == "my.vault"


def test_resolve_passphrase_from_env(config_dir, monkeypatch):
    monkeypatch.setenv("ENVAULT_PASSPHRASE", "secret123")
    assert resolve_passphrase(config_dir) == "secret123"


def test_resolve_passphrase_returns_none_when_unset(config_dir, monkeypatch):
    monkeypatch.delenv("ENVAULT_PASSPHRASE", raising=False)
    assert resolve_passphrase(config_dir) is None
