"""CLI entry point for envault using Click."""

import os
import subprocess
import sys

import click

from envault.vault import inject_vault, load_vault, save_vault

DEFAULT_VAULT_PATH = ".envault"


@click.group()
@click.version_option()
def cli():
    """envault — securely manage and inject environment variables."""


@cli.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--vault", "vault_path", default=DEFAULT_VAULT_PATH, show_default=True, help="Path to vault file.")
@click.password_option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt="Passphrase", help="Vault passphrase.")
def set_var(key, value, vault_path, passphrase):
    """Set a variable KEY=VALUE in the vault."""
    try:
        variables = load_vault(vault_path, passphrase) if os.path.exists(vault_path) else {}
    except Exception as exc:
        raise click.ClickException(f"Failed to load vault: {exc}") from exc

    variables[key] = value
    save_vault(vault_path, variables, passphrase)
    click.echo(f"✔ Set {key} in vault '{vault_path}'.")


@cli.command("get")
@click.argument("key")
@click.option("--vault", "vault_path", default=DEFAULT_VAULT_PATH, show_default=True, help="Path to vault file.")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt="Passphrase", hide_input=True, help="Vault passphrase.")
def get_var(key, vault_path, passphrase):
    """Get the value of KEY from the vault."""
    try:
        variables = load_vault(vault_path, passphrase)
    except Exception as exc:
        raise click.ClickException(f"Failed to load vault: {exc}") from exc

    if key not in variables:
        raise click.ClickException(f"Key '{key}' not found in vault.")
    click.echo(variables[key])


@cli.command("list")
@click.option("--vault", "vault_path", default=DEFAULT_VAULT_PATH, show_default=True, help="Path to vault file.")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt="Passphrase", hide_input=True, help="Vault passphrase.")
def list_vars(vault_path, passphrase):
    """List all variable keys stored in the vault."""
    try:
        variables = load_vault(vault_path, passphrase)
    except Exception as exc:
        raise click.ClickException(f"Failed to load vault: {exc}") from exc

    if not variables:
        click.echo("Vault is empty.")
        return
    for key in sorted(variables):
        click.echo(key)


@cli.command("run")
@click.argument("command", nargs=-1, required=True)
@click.option("--vault", "vault_path", default=DEFAULT_VAULT_PATH, show_default=True, help="Path to vault file.")
@click.option("--passphrase", envvar="ENVAULT_PASSPHRASE", prompt="Passphrase", hide_input=True, help="Vault passphrase.")
def run_command(command, vault_path, passphrase):
    """Run COMMAND with vault variables injected into the environment."""
    try:
        env = inject_vault(vault_path, passphrase)
    except Exception as exc:
        raise click.ClickException(f"Failed to load vault: {exc}") from exc

    result = subprocess.run(list(command), env=env)
    sys.exit(result.returncode)
