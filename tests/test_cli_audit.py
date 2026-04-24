"""Tests for envault.cli_audit commands."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.audit import record_event
from envault.cli_audit import audit_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_path(tmp_path):
    return str(tmp_path / "vault.enc")


def test_show_log_empty(runner, vault_path):
    result = runner.invoke(audit_group, ["log", "--vault", vault_path])
    assert result.exit_code == 0
    assert "No audit events found" in result.output


def test_show_log_displays_events(runner, vault_path):
    record_event(vault_path, "set", key="API_KEY", actor="alice")
    record_event(vault_path, "get", key="DB_URL", actor="alice")
    result = runner.invoke(audit_group, ["log", "--vault", vault_path])
    assert result.exit_code == 0
    assert "set" in result.output
    assert "API_KEY" in result.output
    assert "alice" in result.output


def test_show_log_json_output(runner, vault_path):
    record_event(vault_path, "export", actor="bob")
    result = runner.invoke(audit_group, ["log", "--vault", vault_path, "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["action"] == "export"


def test_show_log_limit(runner, vault_path):
    for i in range(10):
        record_event(vault_path, "set", key=f"VAR_{i}")
    result = runner.invoke(audit_group, ["log", "--vault", vault_path, "--limit", "3", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 3


def test_clear_log_removes_events(runner, vault_path):
    record_event(vault_path, "set", key="X")
    result = runner.invoke(audit_group, ["clear", "--vault", vault_path], input="y\n")
    assert result.exit_code == 0
    assert "cleared" in result.output.lower()


def test_stats_empty(runner, vault_path):
    result = runner.invoke(audit_group, ["stats", "--vault", vault_path])
    assert result.exit_code == 0
    assert "No audit events found" in result.output


def test_stats_shows_counts(runner, vault_path):
    record_event(vault_path, "set", key="A")
    record_event(vault_path, "set", key="B")
    record_event(vault_path, "get", key="A")
    result = runner.invoke(audit_group, ["stats", "--vault", vault_path])
    assert result.exit_code == 0
    assert "Total events : 3" in result.output
    assert "set" in result.output
    assert "get" in result.output
