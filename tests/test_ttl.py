"""Tests for envault.ttl and envault.cli_ttl."""

from __future__ import annotations

import time

import pytest
from click.testing import CliRunner

from envault.ttl import (
    TTLError,
    get_ttl,
    is_expired,
    purge_expired,
    remove_ttl,
    set_ttl,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def simple_vault() -> dict:
    return {"variables": {"API_KEY": "secret", "DB_PASS": "hunter2"}, "meta": {}}


# ---------------------------------------------------------------------------
# Unit tests for ttl.py
# ---------------------------------------------------------------------------

def test_set_ttl_stores_expiry(simple_vault):
    before = time.time()
    updated = set_ttl(simple_vault, "API_KEY", 60)
    expiry = get_ttl(updated, "API_KEY")
    assert expiry is not None
    assert expiry >= before + 59  # allow tiny clock skew
    assert expiry <= before + 61


def test_set_ttl_does_not_mutate_original(simple_vault):
    set_ttl(simple_vault, "API_KEY", 30)
    assert get_ttl(simple_vault, "API_KEY") is None


def test_set_ttl_missing_key_raises(simple_vault):
    with pytest.raises(TTLError, match="not found"):
        set_ttl(simple_vault, "NONEXISTENT", 60)


def test_set_ttl_zero_seconds_raises(simple_vault):
    with pytest.raises(TTLError, match="positive"):
        set_ttl(simple_vault, "API_KEY", 0)


def test_get_ttl_returns_none_when_unset(simple_vault):
    assert get_ttl(simple_vault, "API_KEY") is None


def test_is_expired_false_for_future(simple_vault):
    updated = set_ttl(simple_vault, "API_KEY", 3600)
    assert is_expired(updated, "API_KEY") is False


def test_is_expired_true_for_past(simple_vault):
    updated = set_ttl(simple_vault, "API_KEY", 1)
    # Manually backdate the expiry
    updated["meta"]["__ttl__"]["API_KEY"] = time.time() - 1
    assert is_expired(updated, "API_KEY") is True


def test_is_expired_false_when_no_ttl(simple_vault):
    assert is_expired(simple_vault, "API_KEY") is False


def test_remove_ttl_clears_entry(simple_vault):
    updated = set_ttl(simple_vault, "API_KEY", 60)
    cleared = remove_ttl(updated, "API_KEY")
    assert get_ttl(cleared, "API_KEY") is None


def test_remove_ttl_noop_when_no_ttl(simple_vault):
    result = remove_ttl(simple_vault, "API_KEY")
    assert get_ttl(result, "API_KEY") is None


def test_purge_expired_removes_stale_key(simple_vault):
    updated = set_ttl(simple_vault, "API_KEY", 1)
    updated["meta"]["__ttl__"]["API_KEY"] = time.time() - 1  # already expired
    new_vault, removed = purge_expired(updated)
    assert "API_KEY" not in new_vault["variables"]
    assert removed == ["API_KEY"]


def test_purge_expired_keeps_valid_key(simple_vault):
    updated = set_ttl(simple_vault, "API_KEY", 3600)
    new_vault, removed = purge_expired(updated)
    assert "API_KEY" in new_vault["variables"]
    assert removed == []


def test_purge_expired_returns_empty_list_when_nothing_expired(simple_vault):
    _, removed = purge_expired(simple_vault)
    assert removed == []
