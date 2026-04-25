"""CLI commands for vault locking/unlocking."""

from __future__ import annotations

import json

import click

from .config import resolve_vault_path
from .lock import LockError, get_lock_info, is_locked, lock_vault, unlock_vault


@click.group("lock")
def lock_group() -> None:
    """Lock or unlock a vault to prevent accidental modifications."""


@lock_group.command("set")
@click.option("--vault", default=None, help="Path to vault file.")
@click.option("--reason", default="", help="Reason for locking.")
@click.option("--by", "locked_by", default=None, help="Identity of the locker.")
def lock_cmd(vault: str, reason: str, locked_by: str) -> None:
    """Lock a vault file."""
    vault_path = resolve_vault_path(vault)
    try:
        record = lock_vault(vault_path, reason=reason, locked_by=locked_by)
        click.echo(
            f"Vault locked by '{record['locked_by']}' at {record['locked_at']}."
        )
    except LockError as exc:
        raise click.ClickException(str(exc)) from exc


@lock_group.command("unset")
@click.option("--vault", default=None, help="Path to vault file.")
def unlock_cmd(vault: str) -> None:
    """Unlock a vault file."""
    vault_path = resolve_vault_path(vault)
    try:
        unlock_vault(vault_path)
        click.echo("Vault unlocked.")
    except LockError as exc:
        raise click.ClickException(str(exc)) from exc


@lock_group.command("status")
@click.option("--vault", default=None, help="Path to vault file.")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON.")
def status_cmd(vault: str, as_json: bool) -> None:
    """Show the lock status of a vault."""
    vault_path = resolve_vault_path(vault)
    info = get_lock_info(vault_path)
    if info is None:
        if as_json:
            click.echo(json.dumps({"locked": False}))
        else:
            click.echo("Vault is not locked.")
        return

    if as_json:
        click.echo(json.dumps({"locked": True, **info}, indent=2))
    else:
        click.echo(f"Locked : yes")
        click.echo(f"By     : {info.get('locked_by', 'unknown')}")
        click.echo(f"At     : {info.get('locked_at', '?')}")
        if info.get("reason"):
            click.echo(f"Reason : {info['reason']}")
