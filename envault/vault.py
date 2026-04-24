"""Vault module for reading and writing encrypted .env vault files."""

import json
import os
from typing import Dict

from envault.crypto import encrypt, decrypt

DEFAULT_VAULT_FILE = ".envault"


def load_vault(path: str, passphrase: str) -> Dict[str, str]:
    """Load and decrypt a vault file, returning a dict of env vars.

    Args:
        path: Path to the encrypted vault file.
        passphrase: Passphrase used to decrypt the vault.

    Returns:
        Dictionary of environment variable key-value pairs.

    Raises:
        FileNotFoundError: If the vault file does not exist.
        ValueError: If decryption fails (wrong passphrase or corrupted file).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Vault file not found: {path}")

    with open(path, "r") as f:
        ciphertext = f.read().strip()

    plaintext = decrypt(ciphertext, passphrase)
    return json.loads(plaintext)


def save_vault(path: str, passphrase: str, variables: Dict[str, str]) -> None:
    """Encrypt and save environment variables to a vault file.

    Args:
        path: Path to write the encrypted vault file.
        passphrase: Passphrase used to encrypt the vault.
        variables: Dictionary of environment variable key-value pairs.
    """
    plaintext = json.dumps(variables)
    ciphertext = encrypt(plaintext, passphrase)

    with open(path, "w") as f:
        f.write(ciphertext + "\n")


def inject_vault(path: str, passphrase: str) -> Dict[str, str]:
    """Load vault and inject variables into the current process environment.

    Args:
        path: Path to the encrypted vault file.
        passphrase: Passphrase used to decrypt the vault.

    Returns:
        Dictionary of injected environment variables.
    """
    variables = load_vault(path, passphrase)
    for key, value in variables.items():
        os.environ[key] = value
    return variables
