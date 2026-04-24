"""CLI commands for importing environment variables into a vault."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from envault.audit import record_event
from envault.config import resolve_passphrase, resolve_vault_path
from envault.import_vars import ImportError, import_from_environment, parse_content
from envault.vault import load_vault, save_vault


@click.command("import")
@click.argument("source", required=False, default=None,
                type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--format", "fmt", default=None,
              type=click.Choice(["dotenv", "shell", "json"]),
              help="Force a specific input format (default: auto-detect).")
@click.option("--prefix", default=None,
              help="Only import variables with this prefix (env source only).")
@click.option("--overwrite/--no-overwrite", default=False,
              help="Overwrite existing keys in the vault.")
@click.option("--dry-run", is_flag=True, default=False,
              help="Preview what would be imported without writing.")
@click.option("--vault", "vault_path", default=None, envvar="ENVAULT_VAULT",
              type=click.Path(dir_okay=False, path_type=Path))
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE",
              hide_input=True)
def import_cmd(
    source: Optional[Path],
    fmt: Optional[str],
    prefix: Optional[str],
    overwrite: bool,
    dry_run: bool,
    vault_path: Optional[Path],
    passphrase: Optional[str],
) -> None:
    """Import variables from a file or the current environment into the vault."""
    vault_path = resolve_vault_path(vault_path)
    passphrase = resolve_passphrase(passphrase)

    # Parse incoming variables
    try:
        if source is None:
            incoming = import_from_environment(prefix)
            resolved_fmt = "env"
        else:
            content = source.read_text(encoding="utf-8")
            incoming, resolved_fmt = parse_content(content, fmt)
    except ImportError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    if not incoming:
        click.echo("No variables found to import.")
        return

    # Load existing vault (may be empty)
    existing: dict = {}
    if vault_path.exists():
        try:
            existing = load_vault(vault_path, passphrase)
        except Exception as exc:  # noqa: BLE001
            click.echo(f"Error reading vault: {exc}", err=True)
            sys.exit(1)

    added, skipped = [], []
    merged = dict(existing)
    for key, value in incoming.items():
        if key in existing and not overwrite:
            skipped.append(key)
        else:
            merged[key] = value
            added.append(key)

    if dry_run:
        click.echo(f"[dry-run] Would add/update {len(added)} variable(s): {', '.join(added)}")
        if skipped:
            click.echo(f"[dry-run] Would skip {len(skipped)} existing key(s): {', '.join(skipped)}")
        return

    save_vault(vault_path, passphrase, merged)
    record_event(vault_path, "import", {"format": resolved_fmt, "added": len(added), "skipped": len(skipped)})

    click.echo(f"Imported {len(added)} variable(s) from {source or 'environment'}.")
    if skipped:
        click.echo(f"Skipped {len(skipped)} existing key(s) (use --overwrite to replace).")
