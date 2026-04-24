"""CLI commands for diffing vault contents."""

import json

import click

from envault.config import resolve_passphrase, resolve_vault_path
from envault.diff import diff_vaults


@click.command("diff")
@click.option("--vault", default=None, help="Path to vault file.")
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE", help="Current passphrase.")
@click.option("--compare-passphrase", default=None, help="Passphrase to compare against.")
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json"]), show_default=True)
def diff_cmd(
    vault: str,
    passphrase: str,
    compare_passphrase: str,
    output_format: str,
) -> None:
    """Show differences between vault views (e.g. after rotation)."""
    vault_path = resolve_vault_path(vault)
    passphrase = resolve_passphrase(passphrase)

    if not compare_passphrase:
        click.echo("Error: --compare-passphrase is required.", err=True)
        raise SystemExit(1)

    try:
        result = diff_vaults(vault_path, passphrase, passphrase_b=compare_passphrase)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)

    if output_format == "json":
        data = {
            "added": result.added,
            "removed": result.removed,
            "changed": {k: {"old": v[0], "new": v[1]} for k, v in result.changed.items()},
            "unchanged": result.unchanged,
            "has_changes": result.has_changes,
        }
        click.echo(json.dumps(data, indent=2))
    else:
        if not result.has_changes:
            click.echo("Vaults are identical.")
        else:
            click.echo(result.summary())
