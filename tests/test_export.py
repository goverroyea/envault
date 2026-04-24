"""Tests for envault.export module."""

import json
import pytest

from envault.export import render, SUPPORTED_FORMATS


SAMPLE = {
    "DATABASE_URL": "postgres://localhost/mydb",
    "SECRET_KEY": "s3cr3t",
    "GREETING": "hello world",
}


def test_render_dotenv_contains_all_keys():
    output = render(SAMPLE, "dotenv")
    for key in SAMPLE:
        assert key in output


def test_render_dotenv_format():
    output = render({"FOO": "bar"}, "dotenv")
    assert output.strip() == 'FOO="bar"'


def test_render_dotenv_escapes_double_quotes():
    output = render({"MSG": 'say "hi"'}, "dotenv")
    assert '\\"' in output


def test_render_shell_format():
    output = render({"FOO": "bar"}, "shell")
    assert output.strip() == "FOO='bar'"


def test_render_shell_escapes_single_quotes():
    output = render({"MSG": "it's alive"}, "shell")
    assert "'\\''" in output


def test_render_export_format():
    output = render({"FOO": "bar"}, "export")
    assert output.strip() == "export FOO='bar'"


def test_render_json_is_valid_json():
    output = render(SAMPLE, "json")
    parsed = json.loads(output)
    assert parsed == SAMPLE


def test_render_json_sorted_keys():
    output = render({"Z": "1", "A": "2"}, "json")
    parsed = json.loads(output)
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_render_unsupported_format_raises():
    with pytest.raises(ValueError, match="Unsupported format"):
        render(SAMPLE, "yaml")


def test_render_empty_variables():
    for fmt in SUPPORTED_FORMATS:
        output = render({}, fmt)
        assert isinstance(output, str)


def test_render_dotenv_ends_with_newline():
    output = render({"A": "1"}, "dotenv")
    assert output.endswith("\n")
