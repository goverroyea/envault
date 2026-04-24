"""Export vault variables to various shell-compatible formats."""

from __future__ import annotations

from typing import Dict


SUPPORTED_FORMATS = ("dotenv", "shell", "json", "export")


def format_dotenv(variables: Dict[str, str]) -> str:
    """Format variables as a .env file (KEY=VALUE)."""
    lines = []
    for key, value in sorted(variables.items()):
        escaped = value.replace('"', '\\"')
        lines.append(f'{key}="{escaped}"')
    return "\n".join(lines) + ("\n" if lines else "")


def format_shell(variables: Dict[str, str]) -> str:
    """Format variables as plain shell assignments (KEY=VALUE, no export)."""
    lines = []
    for key, value in sorted(variables.items()):
        escaped = value.replace("'", "'\\''")
        lines.append(f"{key}='{escaped}'")
    return "\n".join(lines) + ("\n" if lines else "")


def format_export(variables: Dict[str, str]) -> str:
    """Format variables as export statements suitable for eval."""
    lines = []
    for key, value in sorted(variables.items()):
        escaped = value.replace("'", "'\\''")
        lines.append(f"export {key}='{escaped}'")
    return "\n".join(lines) + ("\n" if lines else "")


def format_json(variables: Dict[str, str]) -> str:
    """Format variables as a JSON object."""
    import json
    return json.dumps(variables, indent=2, sort_keys=True) + "\n"


def render(variables: Dict[str, str], fmt: str) -> str:
    """Render variables in the requested format.

    Args:
        variables: Mapping of variable names to values.
        fmt: One of 'dotenv', 'shell', 'export', 'json'.

    Returns:
        Formatted string.

    Raises:
        ValueError: If the format is not supported.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )
    dispatch = {
        "dotenv": format_dotenv,
        "shell": format_shell,
        "export": format_export,
        "json": format_json,
    }
    return dispatch[fmt](variables)
