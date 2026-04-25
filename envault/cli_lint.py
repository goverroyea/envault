"""CLI command for linting vault variable names and values."""

from __future__ import annotations

import re
import sys

import click

from envault.config import resolve_passphrase, resolve_vault_path
from envault.lint import lint_vault
from envault.vault import load_vault


@click.command("lint")
@click.option("--vault", "vault_path", default=None, help="Path to the vault file.")
@click.option("--passphrase", default=None, help="Vault passphrase.")
@click.option(
    "--key-pattern",
    default=None,
    help="Regex pattern keys must match (default: UPPER_SNAKE_CASE).",
)
@click.option(
    "--max-value-length",
    default=4096,
    show_default=True,
    help="Maximum allowed value length.",
)
@click.option(
    "--disallow-empty",
    is_flag=True,
    default=False,
    help="Treat empty values as errors.",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Exit non-zero on warnings as well as errors.",
)
def lint_cmd(
    vault_path: str | None,
    passphrase: str | None,
    key_pattern: str | None,
    max_value_length: int,
    disallow_empty: bool,
    strict: bool,
) -> None:
    """Lint variable names and values in the vault."""
    vault_path = resolve_vault_path(vault_path)
    passphrase = resolve_passphrase(passphrase)

    try:
        variables = load_vault(vault_path, passphrase)
    except Exception as exc:  # noqa: BLE001
        click.echo(f"Error loading vault: {exc}", err=True)
        sys.exit(1)

    compiled_pattern = None
    if key_pattern:
        try:
            compiled_pattern = re.compile(key_pattern)
        except re.error as exc:
            click.echo(f"Invalid key pattern: {exc}", err=True)
            sys.exit(1)

    result = lint_vault(
        variables,
        key_pattern=compiled_pattern,
        max_value_length=max_value_length,
        disallow_empty_values=disallow_empty,
    )

    if not result.issues:
        click.echo("No issues found.")
        return

    for issue in result.issues:
        prefix = click.style("[ERROR]" if issue.severity == "error" else "[WARN] ", fg="red" if issue.severity == "error" else "yellow")
        click.echo(f"{prefix} {issue.key}: {issue.message}")

    summary = f"{len(result.errors)} error(s), {len(result.warnings)} warning(s)."
    click.echo(summary)

    if not result.ok or (strict and result.warnings):
        sys.exit(1)
