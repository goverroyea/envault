"""Lint/validate vault variable names and values against configurable rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Default pattern: UPPER_SNAKE_CASE identifiers
DEFAULT_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


@dataclass
class LintIssue:
    key: str
    message: str
    severity: str = "warning"  # "warning" | "error"

    def __repr__(self) -> str:  # pragma: no cover
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def lint_vault(
    variables: Dict[str, str],
    key_pattern: Optional[re.Pattern] = None,
    max_value_length: int = 4096,
    disallow_empty_values: bool = False,
) -> LintResult:
    """Run lint checks on a dict of environment variables.

    Args:
        variables: Mapping of variable name -> value.
        key_pattern: Compiled regex that each key must fully match.
        max_value_length: Maximum allowed length for a value.
        disallow_empty_values: If True, empty string values are an error.

    Returns:
        LintResult containing any discovered issues.
    """
    pattern = key_pattern or DEFAULT_KEY_PATTERN
    result = LintResult()

    for key, value in variables.items():
        # Key naming convention
        if not pattern.fullmatch(key):
            result.issues.append(
                LintIssue(
                    key=key,
                    message=f"Key does not match pattern '{pattern.pattern}'",
                    severity="warning",
                )
            )

        # Empty value check
        if disallow_empty_values and value == "":
            result.issues.append(
                LintIssue(key=key, message="Value is empty", severity="error")
            )

        # Value length check
        if len(value) > max_value_length:
            result.issues.append(
                LintIssue(
                    key=key,
                    message=f"Value exceeds max length of {max_value_length} characters",
                    severity="error",
                )
            )

        # Detect potential unresolved template placeholders
        if re.search(r"\$\{[^}]+\}", value) or re.search(r"%%[^%]+%%", value):
            result.issues.append(
                LintIssue(
                    key=key,
                    message="Value may contain an unresolved placeholder",
                    severity="warning",
                )
            )

    return result
