"""Tests for envault.search and the search CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.search import search_by_key, search_by_value, search_by_tag, SearchResult
from envault.cli_search import search_group
from envault.vault import save_vault


SAMPLE_VARS = {
    "DATABASE_URL": "postgres://localhost/mydb",
    "DATABASE_POOL": "5",
    "REDIS_URL": "redis://localhost:6379",
    "SECRET_KEY": "supersecret",
    "DEBUG": "true",
}


# ---------------------------------------------------------------------------
# Unit tests for search_by_key
# ---------------------------------------------------------------------------

def test_search_by_key_glob_matches():
    results = search_by_key(SAMPLE_VARS, "DATABASE_*")
    keys = {r.key for r in results}
    assert keys == {"DATABASE_URL", "DATABASE_POOL"}


def test_search_by_key_glob_no_match():
    results = search_by_key(SAMPLE_VARS, "MISSING_*")
    assert results == []


def test_search_by_key_regex():
    results = search_by_key(SAMPLE_VARS, r"^(DATABASE|REDIS)_URL$", use_regex=True)
    keys = {r.key for r in results}
    assert keys == {"DATABASE_URL", "REDIS_URL"}


def test_search_by_key_matched_on_field():
    results = search_by_key(SAMPLE_VARS, "DEBUG")
    assert all(r.matched_on == "key" for r in results)


# ---------------------------------------------------------------------------
# Unit tests for search_by_value
# ---------------------------------------------------------------------------

def test_search_by_value_substring():
    results = search_by_value(SAMPLE_VARS, "localhost")
    keys = {r.key for r in results}
    assert keys == {"DATABASE_URL", "REDIS_URL"}


def test_search_by_value_no_match():
    results = search_by_value(SAMPLE_VARS, "nonexistent")
    assert results == []


def test_search_by_value_regex():
    results = search_by_value(SAMPLE_VARS, r"\d+", use_regex=True)
    keys = {r.key for r in results}
    assert "DATABASE_POOL" in keys


def test_search_by_value_matched_on_field():
    results = search_by_value(SAMPLE_VARS, "true")
    assert all(r.matched_on == "value" for r in results)


# ---------------------------------------------------------------------------
# Unit tests for search_by_tag
# ---------------------------------------------------------------------------

def test_search_by_tag_returns_matching_keys():
    tags_meta = {"DATABASE_URL": ["db", "critical"], "SECRET_KEY": ["critical"]}
    results = search_by_tag(SAMPLE_VARS, "critical", tags_meta)
    keys = {r.key for r in results}
    assert keys == {"DATABASE_URL", "SECRET_KEY"}


def test_search_by_tag_no_match():
    tags_meta = {"DATABASE_URL": ["db"]}
    results = search_by_tag(SAMPLE_VARS, "nonexistent", tags_meta)
    assert results == []


def test_search_by_tag_empty_meta():
    results = search_by_tag(SAMPLE_VARS, "anything", {})
    assert results == []


def test_search_by_tag_none_meta():
    results = search_by_tag(SAMPLE_VARS, "anything", None)
    assert results == []


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path):
    path = str(tmp_path / "test.vault")
    save_vault(path, "passphrase", SAMPLE_VARS)
    return path


def test_cli_search_key(runner, vault_path):
    result = runner.invoke(
        search_group,
        ["key", "DATABASE_*", "--vault", vault_path, "--passphrase", "passphrase"],
    )
    assert result.exit_code == 0
    assert "DATABASE_URL" in result.output
    assert "DATABASE_POOL" in result.output


def test_cli_search_key_no_match(runner, vault_path):
    result = runner.invoke(
        search_group,
        ["key", "NOTHING_*", "--vault", vault_path, "--passphrase", "passphrase"],
    )
    assert result.exit_code == 0
    assert "No matches found" in result.output


def test_cli_search_value(runner, vault_path):
    result = runner.invoke(
        search_group,
        ["value", "localhost", "--vault", vault_path, "--passphrase", "passphrase"],
    )
    assert result.exit_code == 0
    assert "DATABASE_URL" in result.output
    assert "REDIS_URL" in result.output


def test_cli_search_tag_no_match(runner, vault_path):
    result = runner.invoke(
        search_group,
        ["tag", "sometag", "--vault", vault_path, "--passphrase", "passphrase"],
    )
    assert result.exit_code == 0
    assert "No matches found" in result.output
