"""Main CLI entry point for envault."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

import click

from envault.audit import record_event
from envault.cli_audit import audit_group
from envault.cli_diff import diff_cmd
from envault.cli_export import export_vars
from envault.cli_import import import_cmd
from envault.cli_rotate import rotate_cmd
from envault.config import resolve_passphrase, resolve_vault_path
from envault.vault import inject_vault, load_vault, save_vault


@click.group()
def cli() -> None:
    """envault — securely manage and inject environment variables."""


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--vault", "vault_path", default=None, envvar="ENVAULT_VAULT",
              type=click.Path(dir_okay=False, path_type=Path))
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE", hide_input=True)
def set_var(key: str, value: str, vault_path: Optional[Path], passphrase: Optional[str]) -> None:
    """Set a variable in the vault."""
    vault_path = resolve_vault_path(vault_path)
    passphrase = resolve_passphrase(passphrase)
    data: dict = {}
    if vault_path.exists():
        data = load_vault(vault_path, passphrase)
    data[key] = value
    save_vault(vault_path, passphrase, data)
    record_event(vault_path, "set", {"key": key})
    click.echo(f"Set {key!r} in {vault_path}.")


@cli.command("get")
@click.argument("key")
@click.option("--vault", "vault_path", default=None, envvar="ENVAULT_VAULT",
              type=click.Path(dir_okay=False, path_type=Path))
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE", hide_input=True)
def get_var(key: str, vault_path: Optional[Path], passphrase: Optional[str]) -> None:
    """Get a variable from the vault."""
    vault_path = resolve_vault_path(vault_path)
    passphrase = resolve_passphrase(passphrase)
    data = load_vault(vault_path, passphrase)
    if key not in data:
        click.echo(f"Key {key!r} not found.", err=True)
        sys.exit(1)
    click.echo(data[key])


@cli.command("list")
@click.option("--vault", "vault_path", default=None, envvar="ENVAULT_VAULT",
              type=click.Path(dir_okay=False, path_type=Path))
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE", hide_input=True)
def list_vars(vault_path: Optional[Path], passphrase: Optional[str]) -> None:
    """List all variable keys in the vault."""
    vault_path = resolve_vault_path(vault_path)
    passphrase = resolve_passphrase(passphrase)
    data = load_vault(vault_path, passphrase)
    for key in sorted(data):
        click.echo(key)


@cli.command("run")
@click.argument("command", nargs=-1, required=True)
@click.option("--vault", "vault_path", default=None, envvar="ENVAULT_VAULT",
              type=click.Path(dir_okay=False, path_type=Path))
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE", hide_input=True)
def run_command(
    command: tuple,
    vault_path: Optional[Path],
    passphrase: Optional[str],
) -> None:
    """Run a command with vault variables injected into the environment."""
    vault_path = resolve_vault_path(vault_path)
    passphrase = resolve_passphrase(passphrase)
    env = inject_vault(vault_path, passphrase)
    result = subprocess.run(list(command), env=env)  # noqa: S603
    sys.exit(result.returncode)


cli.add_command(export_vars, name="export")
cli.add_command(audit_group, name="audit")
cli.add_command(rotate_cmd, name="rotate")
cli.add_command(diff_cmd, name="diff")
cli.add_command(import_cmd, name="import")
