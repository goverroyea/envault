"""Copy variables between vault files."""

from typing import Optional
from envault.vault import load_vault, save_vault
from envault.audit import record_event


class CopyError(Exception):
    """Raised when a vault copy operation fails."""


def copy_vars(
    src_path: str,
    src_passphrase: str,
    dst_path: str,
    dst_passphrase: str,
    keys: Optional[list[str]] = None,
    overwrite: bool = False,
) -> dict:
    """
    Copy variables from one vault to another.

    Args:
        src_path: Path to the source vault file.
        src_passphrase: Passphrase for the source vault.
        dst_path: Path to the destination vault file.
        dst_passphrase: Passphrase for the destination vault.
        keys: Optional list of keys to copy. If None, copies all keys.
        overwrite: If False, raises CopyError on key conflicts.

    Returns:
        A dict with 'copied' and 'skipped' key lists.
    """
    src_data = load_vault(src_path, src_passphrase)
    src_vars = src_data.get("variables", {})

    try:
        dst_data = load_vault(dst_path, dst_passphrase)
    except FileNotFoundError:
        dst_data = {"variables": {}}

    dst_vars = dst_data.get("variables", {})

    selected_keys = keys if keys is not None else list(src_vars.keys())
    missing = [k for k in selected_keys if k not in src_vars]
    if missing:
        raise CopyError(f"Keys not found in source vault: {missing}")

    copied = []
    skipped = []

    for key in selected_keys:
        if key in dst_vars and not overwrite:
            skipped.append(key)
        else:
            dst_vars[key] = src_vars[key]
            copied.append(key)

    dst_data["variables"] = dst_vars
    save_vault(dst_path, dst_passphrase, dst_vars)

    record_event(dst_path, "copy", {"copied": copied, "skipped": skipped, "source": src_path})

    return {"copied": copied, "skipped": skipped}
