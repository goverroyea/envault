"""Tests for envault.template."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.template import (
    TemplateError,
    list_placeholders,
    render_file,
    render_string,
)


# ---------------------------------------------------------------------------
# render_string
# ---------------------------------------------------------------------------

def test_render_string_simple_substitution():
    result = render_string("Hello {{ NAME }}!", {"NAME": "world"})
    assert result == "Hello world!"


def test_render_string_multiple_placeholders():
    tmpl = "{{ HOST }}:{{ PORT }}/{{ PATH }}"
    result = render_string(tmpl, {"HOST": "localhost", "PORT": "5432", "PATH": "db"})
    assert result == "localhost:5432/db"


def test_render_string_repeated_placeholder():
    result = render_string("{{ X }} and {{ X }}", {"X": "42"})
    assert result == "42 and 42"


def test_render_string_extra_variables_ignored():
    result = render_string("{{ A }}", {"A": "1", "B": "2"})
    assert result == "1"


def test_render_string_strict_raises_on_missing():
    with pytest.raises(TemplateError, match="MISSING"):
        render_string("{{ MISSING }}", {}, strict=True)


def test_render_string_non_strict_leaves_placeholder():
    result = render_string("{{ MISSING }}", {}, strict=False)
    assert "{{ MISSING }}" in result


def test_render_string_whitespace_inside_braces():
    result = render_string("{{  KEY  }}", {"KEY": "value"})
    assert result == "value"


def test_render_string_no_placeholders():
    result = render_string("plain text", {})
    assert result == "plain text"


# ---------------------------------------------------------------------------
# list_placeholders
# ---------------------------------------------------------------------------

def test_list_placeholders_returns_sorted_unique():
    tmpl = "{{ B }} {{ A }} {{ B }}"
    assert list_placeholders(tmpl) == ["A", "B"]


def test_list_placeholders_empty_when_none():
    assert list_placeholders("no placeholders here") == []


# ---------------------------------------------------------------------------
# render_file
# ---------------------------------------------------------------------------

def test_render_file_reads_and_substitutes(tmp_path: Path):
    src = tmp_path / "tmpl.txt"
    src.write_text("DB={{ DB_URL }}", encoding="utf-8")
    result = render_file(src, {"DB_URL": "postgres://localhost/mydb"})
    assert result == "DB=postgres://localhost/mydb"


def test_render_file_writes_dest(tmp_path: Path):
    src = tmp_path / "tmpl.env"
    src.write_text("KEY={{ VALUE }}", encoding="utf-8")
    dest = tmp_path / "out" / "rendered.env"
    render_file(src, {"VALUE": "hello"}, dest=dest)
    assert dest.exists()
    assert dest.read_text() == "KEY=hello"


def test_render_file_missing_src_raises(tmp_path: Path):
    with pytest.raises(TemplateError, match="not found"):
        render_file(tmp_path / "nonexistent.txt", {})


def test_render_file_strict_raises_on_missing_key(tmp_path: Path):
    src = tmp_path / "t.txt"
    src.write_text("{{ UNDEFINED }}", encoding="utf-8")
    with pytest.raises(TemplateError):
        render_file(src, {}, strict=True)
