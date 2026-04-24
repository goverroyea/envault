"""CLI command for exporting vault variables to stdout in various formats."""

from __future__ import annotations

import sys

import click

from envault.config import resolve_vault_path, resolve_passphrase
from envault.vault import load_vault
from envault.export import render, SUPPORTED_FORMATS


@click.command("export")
@click.option(
    "--format",
    "fmt",
    default="dotenv",
    show_default=True,
    type=click.Choice(SUPPORTED_FORMATS, case_sensitive=False),
    help="Output format for the exported variables.",
)
@click.option(
    "--vault",
    "vault_path",
    default=None,
    help="Path to the vault file (overrides config).",
)
@click.option(
    "--passphrase",
    default=None,
    help="Passphrase for decryption (overrides config / ENVAULT_PASSPHRASE env var).",
)
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(),
    help="Write output to a file instead of stdout.",
)
def export_vars(fmt: str, vault_path: str | None, passphrase: str | None, output: str | None) -> None:
    """Export vault variables to stdout (or a file) in the chosen format."""
    path = resolve_vault_path(vault_path)
    secret = resolve_passphrase(passphrase)

    try:
        variables = load_vault(path, secret)
    except FileNotFoundError:
        click.echo(f"Vault not found: {path}", err=True)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Failed to load vault: {exc}", err=True)
        sys.exit(1)

    rendered = render(variables, fmt.lower())

    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(rendered)
        click.echo(f"Exported {len(variables)} variable(s) to {output}")
    else:
        click.echo(rendered, nl=False)
