"""Import environment variables into a vault from various sources."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple


class ImportError(Exception):  # noqa: A001
    """Raised when an import operation fails."""


def parse_dotenv(content: str) -> Dict[str, str]:
    """Parse a .env file content into a dictionary."""
    variables: Dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        if key:
            variables[key] = value
    return variables


def parse_shell_export(content: str) -> Dict[str, str]:
    """Parse shell export statements into a dictionary."""
    variables: Dict[str, str] = {}
    pattern = re.compile(r"^export\s+([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
    for line in content.splitlines():
        line = line.strip()
        match = pattern.match(line)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        variables[key] = value
    return variables


def parse_json_env(content: str) -> Dict[str, str]:
    """Parse a JSON object of key/value pairs into a dictionary."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ImportError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ImportError("JSON root must be an object.")
    return {str(k): str(v) for k, v in data.items()}


def import_from_environment(prefix: Optional[str] = None) -> Dict[str, str]:
    """Import variables from the current process environment."""
    env = dict(os.environ)
    if prefix:
        env = {k: v for k, v in env.items() if k.startswith(prefix)}
    return env


def detect_format(content: str) -> str:
    """Heuristically detect the format of the content."""
    stripped = content.strip()
    if stripped.startswith("{"):
        return "json"
    if any(line.strip().startswith("export ") for line in stripped.splitlines()):
        return "shell"
    return "dotenv"


def parse_content(content: str, fmt: Optional[str] = None) -> Tuple[Dict[str, str], str]:
    """Parse content using the given format (or auto-detect)."""
    resolved_fmt = fmt or detect_format(content)
    parsers = {
        "dotenv": parse_dotenv,
        "shell": parse_shell_export,
        "json": parse_json_env,
    }
    if resolved_fmt not in parsers:
        raise ImportError(f"Unknown format: {resolved_fmt!r}. Choose from: {list(parsers)}.")
    return parsers[resolved_fmt](content), resolved_fmt
