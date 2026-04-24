"""Tests for envault/import_vars.py."""

from __future__ import annotations

import os
import pytest

from envault.import_vars import (
    ImportError,
    detect_format,
    import_from_environment,
    parse_content,
    parse_dotenv,
    parse_json_env,
    parse_shell_export,
)


# --- parse_dotenv ---

def test_parse_dotenv_basic():
    content = "KEY=value\nANOTHER=hello"
    result = parse_dotenv(content)
    assert result == {"KEY": "value", "ANOTHER": "hello"}


def test_parse_dotenv_strips_quotes():
    content = 'DB_URL="postgres://localhost/db"\nSECRET=\'mysecret\''
    result = parse_dotenv(content)
    assert result["DB_URL"] == "postgres://localhost/db"
    assert result["SECRET"] == "mysecret"


def test_parse_dotenv_ignores_comments_and_blanks():
    content = "# This is a comment\n\nKEY=value"
    result = parse_dotenv(content)
    assert result == {"KEY": "value"}


def test_parse_dotenv_ignores_lines_without_equals():
    content = "NOEQUALS\nKEY=value"
    result = parse_dotenv(content)
    assert result == {"KEY": "value"}


# --- parse_shell_export ---

def test_parse_shell_export_basic():
    content = "export FOO=bar\nexport BAZ=qux"
    result = parse_shell_export(content)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_shell_export_strips_quotes():
    content = 'export TOKEN="abc123"'
    result = parse_shell_export(content)
    assert result["TOKEN"] == "abc123"


def test_parse_shell_export_ignores_non_export_lines():
    content = "FOO=bar\nexport VALID=yes"
    result = parse_shell_export(content)
    assert result == {"VALID": "yes"}


# --- parse_json_env ---

def test_parse_json_env_basic():
    content = '{"KEY": "value", "NUM": 42}'
    result = parse_json_env(content)
    assert result == {"KEY": "value", "NUM": "42"}


def test_parse_json_env_invalid_json_raises():
    with pytest.raises(ImportError, match="Invalid JSON"):
        parse_json_env("not json")


def test_parse_json_env_non_object_raises():
    with pytest.raises(ImportError, match="must be an object"):
        parse_json_env('["a", "b"]')


# --- detect_format ---

def test_detect_format_json():
    assert detect_format('{"KEY": "val"}') == "json"


def test_detect_format_shell():
    assert detect_format("export FOO=bar") == "shell"


def test_detect_format_dotenv_default():
    assert detect_format("KEY=value") == "dotenv"


# --- parse_content ---

def test_parse_content_auto_detects_dotenv():
    variables, fmt = parse_content("KEY=value")
    assert variables == {"KEY": "value"}
    assert fmt == "dotenv"


def test_parse_content_unknown_format_raises():
    with pytest.raises(ImportError, match="Unknown format"):
        parse_content("KEY=value", fmt="xml")


# --- import_from_environment ---

def test_import_from_environment_returns_dict(monkeypatch):
    monkeypatch.setenv("TEST_ENVAULT_VAR", "hello")
    result = import_from_environment()
    assert "TEST_ENVAULT_VAR" in result
    assert result["TEST_ENVAULT_VAR"] == "hello"


def test_import_from_environment_with_prefix(monkeypatch):
    monkeypatch.setenv("MYAPP_KEY", "val")
    monkeypatch.setenv("OTHER_KEY", "other")
    result = import_from_environment(prefix="MYAPP_")
    assert "MYAPP_KEY" in result
    assert "OTHER_KEY" not in result
