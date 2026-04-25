"""CLI commands for managing variable TTLs."""

from __future__ import annotations

import time

import click

from envault.config import resolve_passphrase, resolve_vault_path
from envault.ttl import TTLError, get_ttl, purge_expired, remove_ttl, set_ttl
from envault.vault import load_vault, save_vault


@click.group("ttl")
def ttl_group() -> None:
    """Manage expiry (TTL) for vault variables."""


@ttl_group.command("set")
@click.argument("key")
@click.argument("seconds", type=int)
@click.option("--vault", "vault_path", default=None, help="Path to vault file.")
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE")
def set_ttl_cmd(key: str, seconds: int, vault_path: str | None, passphrase: str | None) -> None:
    """Set a TTL of SECONDS seconds on KEY."""
    path = resolve_vault_path(vault_path)
    pw = resolve_passphrase(passphrase)
    try:
        vault = load_vault(path, pw)
        updated = set_ttl(vault, key, seconds)
        save_vault(path, updated, pw)
        expiry = get_ttl(updated, key)
        click.echo(f"TTL set: {key!r} expires in {seconds}s (at {expiry:.0f}).")
    except TTLError as exc:
        raise click.ClickException(str(exc)) from exc


@ttl_group.command("get")
@click.argument("key")
@click.option("--vault", "vault_path", default=None)
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE")
def get_ttl_cmd(key: str, vault_path: str | None, passphrase: str | None) -> None:
    """Show remaining TTL for KEY."""
    path = resolve_vault_path(vault_path)
    pw = resolve_passphrase(passphrase)
    vault = load_vault(path, pw)
    expiry = get_ttl(vault, key)
    if expiry is None:
        click.echo(f"{key!r} has no TTL set.")
    else:
        remaining = expiry - time.time()
        if remaining <= 0:
            click.echo(f"{key!r} has EXPIRED.")
        else:
            click.echo(f"{key!r} expires in {remaining:.1f}s.")


@ttl_group.command("remove")
@click.argument("key")
@click.option("--vault", "vault_path", default=None)
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE")
def remove_ttl_cmd(key: str, vault_path: str | None, passphrase: str | None) -> None:
    """Remove the TTL for KEY."""
    path = resolve_vault_path(vault_path)
    pw = resolve_passphrase(passphrase)
    vault = load_vault(path, pw)
    updated = remove_ttl(vault, key)
    save_vault(path, updated, pw)
    click.echo(f"TTL removed from {key!r}.")


@ttl_group.command("purge")
@click.option("--vault", "vault_path", default=None)
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE")
def purge_cmd(vault_path: str | None, passphrase: str | None) -> None:
    """Delete all expired variables from the vault."""
    path = resolve_vault_path(vault_path)
    pw = resolve_passphrase(passphrase)
    vault = load_vault(path, pw)
    updated, removed = purge_expired(vault)
    if removed:
        save_vault(path, updated, pw)
        click.echo(f"Purged {len(removed)} expired key(s): {', '.join(removed)}.")
    else:
        click.echo("No expired keys found.")
