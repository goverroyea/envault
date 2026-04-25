"""Template rendering: substitute vault variables into template strings or files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


class TemplateError(Exception):
    """Raised when template rendering fails."""


_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def render_string(template: str, variables: dict[str, str], strict: bool = True) -> str:
    """Replace ``{{ KEY }}`` placeholders in *template* with values from *variables*.

    Parameters
    ----------
    template:
        The template text containing ``{{ KEY }}`` placeholders.
    variables:
        Mapping of variable names to their values.
    strict:
        When ``True`` (default) raise :class:`TemplateError` for any
        placeholder whose key is not present in *variables*.  When
        ``False`` leave unresolved placeholders unchanged.
    """
    missing: list[str] = []

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1)
        if key in variables:
            return variables[key]
        if strict:
            missing.append(key)
            return match.group(0)
        return match.group(0)

    result = _PLACEHOLDER_RE.sub(_replace, template)

    if missing:
        raise TemplateError(
            f"Template references undefined variable(s): {', '.join(sorted(missing))}"
        )

    return result


def render_file(
    src: Path,
    variables: dict[str, str],
    dest: Optional[Path] = None,
    strict: bool = True,
) -> str:
    """Read *src*, render placeholders, optionally write to *dest*.

    Returns the rendered content as a string regardless of whether *dest*
    is provided.
    """
    if not src.exists():
        raise TemplateError(f"Template file not found: {src}")

    raw = src.read_text(encoding="utf-8")
    rendered = render_string(raw, variables, strict=strict)

    if dest is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(rendered, encoding="utf-8")

    return rendered


def list_placeholders(template: str) -> list[str]:
    """Return a sorted, deduplicated list of placeholder keys in *template*."""
    return sorted(set(_PLACEHOLDER_RE.findall(template)))
