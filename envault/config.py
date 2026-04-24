"""Configuration helpers for envault."""

import json
import os
from pathlib import Path
from typing import Any, Dict

CONFIG_FILENAME = ".envault.config.json"
_DEFAULT_CONFIG: Dict[str, Any] = {
    "vault_path": ".envault",
    "passphrase_env": "ENVAULT_PASSPHRASE",
}


def _config_path(directory: str = ".") -> Path:
    return Path(directory) / CONFIG_FILENAME


def load_config(directory: str = ".") -> Dict[str, Any]:
    """Load project config, falling back to defaults for missing keys."""
    path = _config_path(directory)
    config = dict(_DEFAULT_CONFIG)
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as fh:
                overrides = json.load(fh)
            config.update(overrides)
        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(f"Failed to read config file '{path}': {exc}") from exc
    return config


def save_config(config: Dict[str, Any], directory: str = ".") -> None:
    """Persist config to the project config file."""
    path = _config_path(directory)
    try:
        with path.open("w", encoding="utf-8") as fh:
            json.dump(config, fh, indent=2)
            fh.write("\n")
    except OSError as exc:
        raise ValueError(f"Failed to write config file '{path}': {exc}") from exc


def resolve_vault_path(directory: str = ".") -> str:
    """Return the vault path from config or default."""
    return load_config(directory)["vault_path"]


def resolve_passphrase(directory: str = ".") -> str | None:
    """Return the passphrase from the configured environment variable, or None."""
    config = load_config(directory)
    env_var = config.get("passphrase_env", _DEFAULT_CONFIG["passphrase_env"])
    return os.environ.get(env_var)
