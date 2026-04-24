"""Tests for envault.audit module."""

import json
from pathlib import Path

import pytest

from envault.audit import record_event, read_events, clear_events, _audit_log_path


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.enc")


def test_record_event_creates_log_file(vault_path):
    record_event(vault_path, "set", key="API_KEY")
    log_path = _audit_log_path(vault_path)
    assert log_path.exists()


def test_record_event_writes_valid_json(vault_path):
    record_event(vault_path, "get", key="DB_URL")
    log_path = _audit_log_path(vault_path)
    line = log_path.read_text().strip()
    event = json.loads(line)
    assert event["action"] == "get"
    assert event["key"] == "DB_URL"


def test_record_event_includes_timestamp(vault_path):
    record_event(vault_path, "list")
    events = read_events(vault_path)
    assert "timestamp" in events[0]
    assert "T" in events[0]["timestamp"]  # ISO format check


def test_record_event_includes_vault_path(vault_path):
    record_event(vault_path, "export")
    events = read_events(vault_path)
    assert events[0]["vault"].endswith("vault.enc")


def test_record_event_custom_actor(vault_path):
    record_event(vault_path, "delete", key="SECRET", actor="ci-bot")
    events = read_events(vault_path)
    assert events[0]["actor"] == "ci-bot"


def test_read_events_returns_empty_list_when_no_log(vault_path):
    result = read_events(vault_path)
    assert result == []


def test_read_events_returns_all_events(vault_path):
    record_event(vault_path, "set", key="A")
    record_event(vault_path, "set", key="B")
    record_event(vault_path, "get", key="A")
    events = read_events(vault_path)
    assert len(events) == 3


def test_clear_events_removes_log(vault_path):
    record_event(vault_path, "set", key="X")
    clear_events(vault_path)
    assert not _audit_log_path(vault_path).exists()


def test_clear_events_no_error_when_no_log(vault_path):
    # Should not raise even if no log exists
    clear_events(vault_path)
