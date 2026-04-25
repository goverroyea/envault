"""Tests for envault.lint and the lint CLI command."""

from __future__ import annotations

import re

import pytest
from click.testing import CliRunner

from envault.lint import LintIssue, LintResult, lint_vault
from envault.cli_lint import lint_cmd
from envault.vault import save_vault


# ---------------------------------------------------------------------------
# Unit tests for lint_vault()
# ---------------------------------------------------------------------------


def test_lint_clean_vault_returns_no_issues():
    variables = {"DB_HOST": "localhost", "API_KEY": "secret123"}
    result = lint_vault(variables)
    assert result.issues == []
    assert result.ok is True


def test_lint_lowercase_key_produces_warning():
    result = lint_vault({"db_host": "localhost"})
    assert len(result.warnings) == 1
    assert result.warnings[0].key == "db_host"
    assert result.ok is True  # warnings don't affect ok


def test_lint_empty_value_error_when_disallowed():
    result = lint_vault({"API_KEY": ""}, disallow_empty_values=True)
    assert any(i.severity == "error" and i.key == "API_KEY" for i in result.issues)
    assert result.ok is False


def test_lint_empty_value_ok_by_default():
    result = lint_vault({"API_KEY": ""})
    errors = [i for i in result.issues if i.severity == "error"]
    assert errors == []


def test_lint_value_too_long():
    long_value = "x" * 5000
    result = lint_vault({"BIG_VAR": long_value})
    assert any(i.severity == "error" and "max length" in i.message for i in result.issues)


def test_lint_custom_max_value_length():
    result = lint_vault({"SHORT": "hello"}, max_value_length=3)
    assert any("max length" in i.message for i in result.issues)


def test_lint_detects_unresolved_placeholder_curly():
    result = lint_vault({"URL": "https://example.com/${HOST}/path"})
    assert any("placeholder" in i.message for i in result.issues)


def test_lint_detects_unresolved_placeholder_percent():
    result = lint_vault({"URL": "https://%%HOST%%/path"})
    assert any("placeholder" in i.message for i in result.issues)


def test_lint_custom_key_pattern():
    pattern = re.compile(r"^[a-z][a-z0-9_]*$")
    result = lint_vault({"my_var": "value", "BAD_VAR": "value"}, key_pattern=pattern)
    keys_with_issues = {i.key for i in result.issues}
    assert "BAD_VAR" in keys_with_issues
    assert "my_var" not in keys_with_issues


def test_lint_result_ok_false_when_errors():
    result = LintResult(issues=[LintIssue(key="X", message="bad", severity="error")])
    assert result.ok is False


# ---------------------------------------------------------------------------
# CLI tests for lint_cmd
# ---------------------------------------------------------------------------


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    path = str(tmp_path / "test.vault")
    save_vault(path, "passphrase", {"DB_HOST": "localhost", "API_KEY": "s3cr3t"})
    return path


def test_cli_lint_clean_vault(runner, vault_path):
    result = runner.invoke(
        lint_cmd, ["--vault", vault_path, "--passphrase", "passphrase"]
    )
    assert result.exit_code == 0
    assert "No issues found" in result.output


def test_cli_lint_warns_on_lowercase_key(runner, tmp_path):
    path = str(tmp_path / "v.vault")
    save_vault(path, "pass", {"lower_key": "value"})
    result = runner.invoke(lint_cmd, ["--vault", path, "--passphrase", "pass"])
    assert result.exit_code == 0  # warnings only
    assert "lower_key" in result.output


def test_cli_lint_strict_exits_nonzero_on_warnings(runner, tmp_path):
    path = str(tmp_path / "v.vault")
    save_vault(path, "pass", {"lower_key": "value"})
    result = runner.invoke(
        lint_cmd, ["--vault", path, "--passphrase", "pass", "--strict"]
    )
    assert result.exit_code != 0


def test_cli_lint_invalid_pattern_exits_nonzero(runner, vault_path):
    result = runner.invoke(
        lint_cmd,
        ["--vault", vault_path, "--passphrase", "passphrase", "--key-pattern", "[invalid"],
    )
    assert result.exit_code != 0
