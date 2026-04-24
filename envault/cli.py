"""CLI entry point for envault."""

from __future__ import annotations

import sys

import click

from envault.config import resolve_vault_path, resolve_passphrase
from envault.vault import load_vault, save_vault, inject_vault
from envault.cli_export import export_vars


@click.group()
def cli() -> None:
    """envault — securely manage and inject environment variables."""


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--vault", "vault_path", default=None)
@click.option("--passphrase", default=None)
def set_var(key: str, value: str, vault_path: str | None, passphrase: str | None) -> None:
    """Set a variable in the vault."""
    path = resolve_vault_path(vault_path)
    secret = resolve_passphrase(passphrase)
    try:
        variables = load_vault(path, secret)
    except FileNotFoundError:
        variables = {}
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error loading vault: {exc}", err=True)
        sys.exit(1)
    variables[key] = value
    save_vault(path, secret, variables)
    click.echo(f"Set {key} in {path}")


@cli.command("get")
@click.argument("key")
@click.option("--vault", "vault_path", default=None)
@click.option("--passphrase", default=None)
def get_var(key: str, vault_path: str | None, passphrase: str | None) -> None:
    """Get a variable from the vault."""
    path = resolve_vault_path(vault_path)
    secret = resolve_passphrase(passphrase)
    try:
        variables = load_vault(path, secret)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    if key not in variables:
        click.echo(f"Key '{key}' not found.", err=True)
        sys.exit(1)
    click.echo(variables[key])


@cli.command("list")
@click.option("--vault", "vault_path", default=None)
@click.option("--passphrase", default=None)
def list_vars(vault_path: str | None, passphrase: str | None) -> None:
    """List all variable keys in the vault."""
    path = resolve_vault_path(vault_path)
    secret = resolve_passphrase(passphrase)
    try:
        variables = load_vault(path, secret)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    for key in sorted(variables):
        click.echo(key)


@cli.command("run")
@click.argument("command", nargs=-1, required=True)
@click.option("--vault", "vault_path", default=None)
@click.option("--passphrase", default=None)
def run_command(command: tuple[str, ...], vault_path: str | None, passphrase: str | None) -> None:
    """Run a command with vault variables injected into the environment."""
    path = resolve_vault_path(vault_path)
    secret = resolve_passphrase(passphrase)
    try:
        inject_vault(path, secret, list(command))
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


cli.add_command(export_vars)
