"""Merge variables from one vault into another."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.vault import load_vault, save_vault


class MergeError(Exception):
    """Raised when a merge operation fails."""


@dataclass
class MergeResult:
    added: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.overwritten)


def merge_vaults(
    src_path: str,
    src_passphrase: str,
    dst_path: str,
    dst_passphrase: str,
    *,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
    dry_run: bool = False,
) -> MergeResult:
    """Merge variables from *src* vault into *dst* vault.

    Args:
        src_path: Path to the source vault file.
        src_passphrase: Passphrase for the source vault.
        dst_path: Path to the destination vault file.
        dst_passphrase: Passphrase for the destination vault.
        keys: Optional list of keys to merge; if None, all keys are merged.
        overwrite: If True, overwrite existing keys in destination.
        dry_run: If True, compute the result without writing changes.

    Returns:
        A :class:`MergeResult` describing what was added, overwritten, or skipped.
    """
    src_vars: Dict[str, str] = load_vault(src_path, src_passphrase)
    try:
        dst_vars: Dict[str, str] = load_vault(dst_path, dst_passphrase)
    except FileNotFoundError:
        dst_vars = {}

    candidates = {k: v for k, v in src_vars.items() if keys is None or k in keys}

    if keys:
        missing = set(keys) - set(src_vars)
        if missing:
            raise MergeError(
                f"Keys not found in source vault: {', '.join(sorted(missing))}"
            )

    result = MergeResult()
    merged = dict(dst_vars)

    for key, value in candidates.items():
        if key in dst_vars:
            if overwrite:
                merged[key] = value
                result.overwritten.append(key)
            else:
                result.skipped.append(key)
        else:
            merged[key] = value
            result.added.append(key)

    if not dry_run and result.total_changes > 0:
        save_vault(dst_path, dst_passphrase, merged)

    return result
