"""Diff utilities for comparing vault contents across passphrases or snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.vault import load_vault


@dataclass
class VaultDiff:
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (old, new)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = []
        for key, value in sorted(self.added.items()):
            lines.append(f"+ {key}={value}")
        for key, value in sorted(self.removed.items()):
            lines.append(f"- {key}={value}")
        for key, (old, new) in sorted(self.changed.items()):
            lines.append(f"~ {key}: {old!r} -> {new!r}")
        for key in sorted(self.unchanged):
            lines.append(f"  {key}")
        return "\n".join(lines) if lines else "(no variables)"


def diff_vaults(
    vault_path: str,
    passphrase_a: str,
    passphrase_b: Optional[str] = None,
    snapshot: Optional[Dict[str, str]] = None,
) -> VaultDiff:
    """Compare vault contents decrypted with passphrase_a against either
    the same vault decrypted with passphrase_b, or a provided snapshot dict."""
    vars_a = load_vault(vault_path, passphrase_a)

    if snapshot is not None:
        vars_b = snapshot
    elif passphrase_b is not None:
        vars_b = load_vault(vault_path, passphrase_b)
    else:
        raise ValueError("Provide either passphrase_b or snapshot.")

    result = VaultDiff()
    all_keys = set(vars_a) | set(vars_b)

    for key in all_keys:
        in_a = key in vars_a
        in_b = key in vars_b
        if in_a and not in_b:
            result.removed[key] = vars_a[key]
        elif in_b and not in_a:
            result.added[key] = vars_b[key]
        elif vars_a[key] != vars_b[key]:
            result.changed[key] = (vars_a[key], vars_b[key])
        else:
            result.unchanged.append(key)

    return result
