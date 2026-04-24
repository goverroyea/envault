"""Main CLI entry point for envault."""

import subprocess
import sys

import click

from envault.config import resolve_vault_path, resolve_passphrase
from envault.vault import load_vault, save_vault, inject_vault
from envault.audit import record_event
from envault.cli_export import export_vars
from envault.cli_audit import audit_group


@click.group()
def cli():
    """envault — secure environment variable management."""


cli.add_command(export_vars, name="export")
cli.add_command(audit_group, name="audit")


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--vault", default=None, help="Path to vault file.")
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE", help="Vault passphrase.")
def set_var(key, value, vault, passphrase):
    """Set a variable in the vault."""
    vault_path = resolve_vault_path(vault)
    passphrase = resolve_passphrase(passphrase)
    try:
        variables = load_vault(vault_path, passphrase)
    except FileNotFoundError:
        variables = {}
    variables[key] = value
    save_vault(vault_path, variables, passphrase)
    record_event(vault_path, "set", key=key)
    click.echo(f"Set {key}")


@cli.command("get")
@click.argument("key")
@click.option("--vault", default=None, help="Path to vault file.")
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE", help="Vault passphrase.")
def get_var(key, vault, passphrase):
    """Get a variable from the vault."""
    vault_path = resolve_vault_path(vault)
    passphrase = resolve_passphrase(passphrase)
    variables = load_vault(vault_path, passphrase)
    if key not in variables:
        click.echo(f"Key '{key}' not found.", err=True)
        sys.exit(1)
    record_event(vault_path, "get", key=key)
    click.echo(variables[key])


@cli.command("list")
@click.option("--vault", default=None, help="Path to vault file.")
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE", help="Vault passphrase.")
def list_vars(vault, passphrase):
    """List all variable names in the vault."""
    vault_path = resolve_vault_path(vault)
    passphrase = resolve_passphrase(passphrase)
    variables = load_vault(vault_path, passphrase)
    record_event(vault_path, "list")
    if not variables:
        click.echo("No variables stored.")
        return
    for key in sorted(variables):
        click.echo(key)


@cli.command("run")
@click.argument("command", nargs=-1, required=True)
@click.option("--vault", default=None, help="Path to vault file.")
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE", help="Vault passphrase.")
def run_command(command, vault, passphrase):
    """Run a command with vault variables injected into the environment."""
    vault_path = resolve_vault_path(vault)
    passphrase = resolve_passphrase(passphrase)
    env = inject_vault(vault_path, passphrase)
    record_event(vault_path, "run")
    result = subprocess.run(list(command), env=env)
    sys.exit(result.returncode)


if __name__ == "__main__":
    cli()
