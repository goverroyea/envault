"""CLI commands for inspecting per-key change history."""

import json

import click

from envault.config import resolve_passphrase, resolve_vault_path
from envault.history import clear_history, get_history
from envault.vault import load_vault, save_vault


@click.group("history")
def history_group() -> None:
    """Commands for viewing and managing key change history."""


@history_group.command("show")
@click.argument("key")
@click.option("--vault", "vault_path", default=None, help="Path to vault file.")
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE")
@click.option("--json", "as_json", is_flag=True, default=False)
def show_history(key: str, vault_path: str | None, passphrase: str | None, as_json: bool) -> None:
    """Show change history for KEY."""
    vault_path = resolve_vault_path(vault_path)
    passphrase = resolve_passphrase(passphrase)
    vault = load_vault(vault_path, passphrase)
    entries = get_history(vault, key)

    if not entries:
        click.echo(f"No history found for '{key}'.")
        return

    if as_json:
        click.echo(json.dumps(entries, indent=2))
    else:
        click.echo(f"History for '{key}' ({len(entries)} entries):")
        for e in entries:
            old = e.get("old") or "(unset)"
            new = e.get("new") or "(unset)"
            click.echo(f"  [{e['ts']}]  {old!r} -> {new!r}")


@history_group.command("clear")
@click.argument("key", required=False, default=None)
@click.option("--vault", "vault_path", default=None, help="Path to vault file.")
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE")
@click.option("--all", "all_keys", is_flag=True, default=False, help="Clear history for all keys.")
def clear_history_cmd(
    key: str | None, vault_path: str | None, passphrase: str | None, all_keys: bool
) -> None:
    """Clear change history for KEY (or all keys with --all)."""
    if not key and not all_keys:
        raise click.UsageError("Provide KEY or use --all to clear all history.")

    vault_path = resolve_vault_path(vault_path)
    passphrase = resolve_passphrase(passphrase)
    vault = load_vault(vault_path, passphrase)
    updated = clear_history(vault, key if not all_keys else None)
    save_vault(vault_path, updated, passphrase)

    if all_keys:
        click.echo("Cleared history for all keys.")
    else:
        click.echo(f"Cleared history for '{key}'.")
