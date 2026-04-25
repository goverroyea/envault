"""CLI commands for searching vault variables."""

from __future__ import annotations

import click

from .audit import record_event
from .config import resolve_passphrase, resolve_vault_path
from .search import search_by_key, search_by_value, search_by_tag
from .vault import load_vault


@click.group("search")
def search_group() -> None:
    """Search vault variables by key, value, or tag."""


@search_group.command("key")
@click.argument("pattern")
@click.option("--vault", default=None, help="Path to the vault file.")
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE", help="Vault passphrase.")
@click.option("--regex", is_flag=True, default=False, help="Treat PATTERN as a regular expression.")
def search_key(pattern: str, vault: str, passphrase: str, regex: bool) -> None:
    """Search variables by key name (glob or regex)."""
    vault_path = resolve_vault_path(vault)
    passphrase = resolve_passphrase(passphrase)
    variables, _ = load_vault(vault_path, passphrase)
    results = search_by_key(variables, pattern, use_regex=regex)
    if not results:
        click.echo("No matches found.")
        return
    for r in results:
        click.echo(f"{r.key}={r.value}")
    record_event(vault_path, "search", {"field": "key", "pattern": pattern, "matches": len(results)})


@search_group.command("value")
@click.argument("pattern")
@click.option("--vault", default=None, help="Path to the vault file.")
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE", help="Vault passphrase.")
@click.option("--regex", is_flag=True, default=False, help="Treat PATTERN as a regular expression.")
def search_value(pattern: str, vault: str, passphrase: str, regex: bool) -> None:
    """Search variables whose value contains PATTERN."""
    vault_path = resolve_vault_path(vault)
    passphrase = resolve_passphrase(passphrase)
    variables, _ = load_vault(vault_path, passphrase)
    results = search_by_value(variables, pattern, use_regex=regex)
    if not results:
        click.echo("No matches found.")
        return
    for r in results:
        click.echo(f"{r.key}={r.value}")
    record_event(vault_path, "search", {"field": "value", "pattern": pattern, "matches": len(results)})


@search_group.command("tag")
@click.argument("tag")
@click.option("--vault", default=None, help="Path to the vault file.")
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE", help="Vault passphrase.")
def search_tag(tag: str, vault: str, passphrase: str) -> None:
    """Search variables that carry TAG."""
    vault_path = resolve_vault_path(vault)
    passphrase = resolve_passphrase(passphrase)
    variables, meta = load_vault(vault_path, passphrase)
    tags_meta: dict = meta.get("tags", {})
    results = search_by_tag(variables, tag, tags_meta)
    if not results:
        click.echo("No matches found.")
        return
    for r in results:
        click.echo(f"{r.key}={r.value}")
    record_event(vault_path, "search", {"field": "tag", "tag": tag, "matches": len(results)})
