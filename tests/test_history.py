"""Tests for envault.history."""

import pytest

from envault.history import (
    MAX_HISTORY,
    clear_history,
    get_history,
    record_change,
)


BASE_VAULT: dict = {"vars": {"FOO": "bar"}}


def test_record_change_adds_entry() -> None:
    vault = record_change(BASE_VAULT, "FOO", None, "bar")
    entries = get_history(vault, "FOO")
    assert len(entries) == 1
    assert entries[0]["old"] is None
    assert entries[0]["new"] == "bar"


def test_record_change_multiple_entries_ordered() -> None:
    vault = BASE_VAULT
    vault = record_change(vault, "FOO", None, "v1")
    vault = record_change(vault, "FOO", "v1", "v2")
    entries = get_history(vault, "FOO")
    assert len(entries) == 2
    assert entries[0]["new"] == "v1"
    assert entries[1]["new"] == "v2"


def test_record_change_does_not_mutate_original() -> None:
    original = dict(BASE_VAULT)
    record_change(original, "FOO", None, "changed")
    assert "__meta__" not in original


def test_record_change_includes_timestamp() -> None:
    vault = record_change(BASE_VAULT, "KEY", "old", "new")
    entry = get_history(vault, "KEY")[0]
    assert "ts" in entry
    assert entry["ts"].endswith("Z")


def test_record_change_caps_at_max_history() -> None:
    vault: dict = {}
    for i in range(MAX_HISTORY + 5):
        vault = record_change(vault, "K", str(i), str(i + 1))
    entries = get_history(vault, "K")
    assert len(entries) == MAX_HISTORY
    # Most recent entry should be the last recorded
    assert entries[-1]["new"] == str(MAX_HISTORY + 5)


def test_get_history_returns_empty_for_unknown_key() -> None:
    assert get_history(BASE_VAULT, "NONEXISTENT") == []


def test_clear_history_removes_specific_key() -> None:
    vault = record_change(BASE_VAULT, "FOO", None, "bar")
    vault = record_change(vault, "BAZ", None, "qux")
    vault = clear_history(vault, "FOO")
    assert get_history(vault, "FOO") == []
    assert len(get_history(vault, "BAZ")) == 1


def test_clear_history_removes_all_keys() -> None:
    vault = record_change(BASE_VAULT, "FOO", None, "bar")
    vault = record_change(vault, "BAZ", None, "qux")
    vault = clear_history(vault, None)
    assert get_history(vault, "FOO") == []
    assert get_history(vault, "BAZ") == []


def test_clear_history_no_op_on_missing_key() -> None:
    vault = clear_history(BASE_VAULT, "MISSING")
    # Should not raise and __meta__ history should be empty
    assert get_history(vault, "MISSING") == []
