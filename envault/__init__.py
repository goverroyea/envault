"""envault — Securely manage and inject environment variables."""

from envault.vault import load_vault, save_vault, inject_vault

__all__ = ["load_vault", "save_vault", "inject_vault"]
__version__ = "0.1.0"
