"""CLI commands for viewing and managing the audit log."""

import json
from datetime import datetime

import click

from envault.audit import read_events, clear_events
from envault.config import resolve_vault_path


@click.group("audit")
def audit_group():
    """View and manage the vault audit log."""


@audit_group.command("log")
@click.option("--vault", default=None, help="Path to vault file.")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output as JSON.")
@click.option("--limit", default=50, show_default=True, help="Maximum number of events to show.")
def show_log(vault, as_json, limit):
    """Display recent audit log entries."""
    vault_path = resolve_vault_path(vault)
    events = read_events(vault_path)
    recent = events[-limit:] if len(events) > limit else events

    if not recent:
        click.echo("No audit events found.")
        return

    if as_json:
        click.echo(json.dumps(recent, indent=2))
    else:
        for event in recent:
            ts = event.get("timestamp", "?")
            action = event.get("action", "?")
            key = event.get("key") or "-"
            actor = event.get("actor", "?")
            click.echo(f"{ts}  [{actor}]  {action:<10}  {key}")


@audit_group.command("clear")
@click.option("--vault", default=None, help="Path to vault file.")
@click.confirmation_option(prompt="Clear the entire audit log?")
def clear_log(vault):
    """Delete all audit log entries."""
    vault_path = resolve_vault_path(vault)
    clear_events(vault_path)
    click.echo("Audit log cleared.")


@audit_group.command("stats")
@click.option("--vault", default=None, help="Path to vault file.")
def show_stats(vault):
    """Show summary statistics for the audit log."""
    vault_path = resolve_vault_path(vault)
    events = read_events(vault_path)

    if not events:
        click.echo("No audit events found.")
        return

    action_counts: dict[str, int] = {}
    for event in events:
        action = event.get("action", "unknown")
        action_counts[action] = action_counts.get(action, 0) + 1

    click.echo(f"Total events : {len(events)}")
    click.echo("By action:")
    for action, count in sorted(action_counts.items()):
        click.echo(f"  {action:<12} {count}")
