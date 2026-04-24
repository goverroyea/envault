"""Passphrase rotation for envault vaults."""

from pathlib import Path
from typing import Optional

from envault.vault import load_vault, save_vault
from envault.audit import record_event


class RotationError(Exception):
    """Raised when vault rotation fails."""


def rotate_passphrase(
    vault_path: Path,
    old_passphrase: str,
    new_passphrase: str,
    *,
    audit: bool = True,
) -> int:
    """Re-encrypt an existing vault with a new passphrase.

    Loads all variables using *old_passphrase*, then immediately
    re-saves them encrypted with *new_passphrase*.

    Returns the number of variables that were rotated.

    Raises
    ------
    RotationError
        If the old passphrase is wrong or the vault file is missing.
    ValueError
        If old and new passphrases are identical.
    """
    if old_passphrase == new_passphrase:
        raise ValueError("New passphrase must differ from the old passphrase.")

    if not vault_path.exists():
        raise RotationError(f"Vault not found: {vault_path}")

    try:
        variables = load_vault(vault_path, old_passphrase)
    except Exception as exc:  # noqa: BLE001
        raise RotationError(f"Failed to decrypt vault with old passphrase: {exc}") from exc

    save_vault(vault_path, variables, new_passphrase)

    if audit:
        record_event(
            vault_path,
            "rotate",
            {"variables_count": len(variables)},
        )

    return len(variables)
