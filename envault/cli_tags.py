"""CLI commands for managing variable tags."""
import click

from envault.config import resolve_vault_path, resolve_passphrase
from envault.vault import load_vault, save_vault
from envault import tags as tag_ops


@click.group("tags")
def tags_group() -> None:
    """Manage tags on vault variables."""


@tags_group.command("set")
@click.argument("key")
@click.argument("tag", nargs=-1, required=True)
@click.option("--vault", default=None, help="Path to vault file.")
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE")
def set_tag(key: str, tag: tuple, vault: str, passphrase: str) -> None:
    """Attach one or more TAGs to a variable KEY."""
    vault_path = resolve_vault_path(vault)
    pw = resolve_passphrase(passphrase)
    variables = load_vault(vault_path, pw)
    if key not in variables or key == tag_ops.TAGS_KEY:
        raise click.ClickException(f"Variable '{key}' not found in vault.")
    existing = tag_ops.get_tags(variables, key)
    updated = tag_ops.set_tags(variables, key, existing + list(tag))
    save_vault(vault_path, pw, updated)
    click.echo(f"Tags for '{key}': {', '.join(tag_ops.get_tags(updated, key))}")


@tags_group.command("remove")
@click.argument("key")
@click.option("--vault", default=None)
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE")
def remove_tag(key: str, vault: str, passphrase: str) -> None:
    """Remove all tags from variable KEY."""
    vault_path = resolve_vault_path(vault)
    pw = resolve_passphrase(passphrase)
    variables = load_vault(vault_path, pw)
    updated = tag_ops.remove_tags(variables, key)
    save_vault(vault_path, pw, updated)
    click.echo(f"Tags removed from '{key}'.")


@tags_group.command("list")
@click.argument("key", required=False)
@click.option("--vault", default=None)
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE")
def list_tags(key: str, vault: str, passphrase: str) -> None:
    """List tags for KEY, or all tags if no key is given."""
    vault_path = resolve_vault_path(vault)
    pw = resolve_passphrase(passphrase)
    variables = load_vault(vault_path, pw)
    if key:
        t = tag_ops.get_tags(variables, key)
        click.echo(", ".join(t) if t else f"No tags for '{key}'.")
    else:
        all_tags = tag_ops.list_all_tags(variables)
        click.echo(", ".join(all_tags) if all_tags else "No tags defined.")


@tags_group.command("filter")
@click.argument("tag")
@click.option("--vault", default=None)
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE")
def filter_tag(tag: str, vault: str, passphrase: str) -> None:
    """List variables that have TAG."""
    vault_path = resolve_vault_path(vault)
    pw = resolve_passphrase(passphrase)
    variables = load_vault(vault_path, pw)
    matched = tag_ops.filter_by_tag(variables, tag)
    if not matched:
        click.echo(f"No variables tagged '{tag}'.")
    else:
        for k in sorted(matched):
            click.echo(k)
