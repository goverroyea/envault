"""CLI command for rotating the vault passphrase."""

import click

from envault.config import resolve_vault_path, resolve_passphrase
from envault.rotate import rotate_passphrase, RotationError


@click.command("rotate")
@click.option(
    "--vault",
    "vault_path_override",
    default=None,
    help="Path to the vault file (overrides config).",
)
@click.option(
    "--passphrase",
    "old_passphrase_override",
    default=None,
    envvar="ENVAULT_PASSPHRASE",
    help="Current passphrase (overrides config / env var).",
)
@click.option(
    "--new-passphrase",
    "new_passphrase",
    default=None,
    envvar="ENVAULT_NEW_PASSPHRASE",
    help="New passphrase to encrypt the vault with.",
)
def rotate_cmd(
    vault_path_override: str | None,
    old_passphrase_override: str | None,
    new_passphrase: str | None,
) -> None:
    """Re-encrypt the vault with a new passphrase."""
    vault_path = resolve_vault_path(vault_path_override)
    old_passphrase = resolve_passphrase(old_passphrase_override)

    if not old_passphrase:
        raise click.UsageError(
            "Current passphrase is required. Use --passphrase or set ENVAULT_PASSPHRASE."
        )

    if not new_passphrase:
        new_passphrase = click.prompt(
            "New passphrase",
            hide_input=True,
            confirmation_prompt=True,
        )

    try:
        count = rotate_passphrase(vault_path, old_passphrase, new_passphrase)
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc
    except RotationError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Rotated passphrase for {vault_path} ({count} variable(s) re-encrypted).")
