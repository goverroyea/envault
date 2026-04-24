import click
from envault.snapshot import create_snapshot, list_snapshots, restore_snapshot, SnapshotError
from envault.config import resolve_vault_path, resolve_passphrase
from envault.audit import record_event


@click.group("snapshot")
def snapshot_group():
    """Manage vault snapshots."""
    pass


@snapshot_group.command("create")
@click.option("--vault", default=None, help="Path to vault file.")
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE", help="Vault passphrase.")
@click.option("--label", default=None, help="Optional label for the snapshot.")
def create_cmd(vault, passphrase, label):
    """Create a snapshot of the current vault."""
    vault_path = resolve_vault_path(vault)
    passphrase = resolve_passphrase(passphrase)
    try:
        snapshot_id = create_snapshot(vault_path, passphrase, label=label)
        record_event(vault_path, "snapshot_create", {"snapshot_id": snapshot_id, "label": label})
        click.echo(f"Snapshot created: {snapshot_id}")
    except SnapshotError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@snapshot_group.command("list")
@click.option("--vault", default=None, help="Path to vault file.")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON.")
def list_cmd(vault, output_json):
    """List all available snapshots."""
    vault_path = resolve_vault_path(vault)
    snapshots = list_snapshots(vault_path)
    if not snapshots:
        click.echo("No snapshots found.")
        return
    if output_json:
        import json
        click.echo(json.dumps(snapshots, indent=2))
    else:
        for snap in snapshots:
            label_str = f"  [{snap['label']}]" if snap.get("label") else ""
            click.echo(f"{snap['id']}  {snap['created_at']}{label_str}  ({snap['var_count']} vars)")


@snapshot_group.command("restore")
@click.argument("snapshot_id")
@click.option("--vault", default=None, help="Path to vault file.")
@click.option("--passphrase", default=None, envvar="ENVAULT_PASSPHRASE", help="Vault passphrase.")
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt.")
def restore_cmd(snapshot_id, vault, passphrase, confirm):
    """Restore vault from a snapshot."""
    vault_path = resolve_vault_path(vault)
    passphrase = resolve_passphrase(passphrase)
    if not confirm:
        click.confirm(
            f"Restore snapshot '{snapshot_id}'? This will overwrite the current vault.",
            abort=True,
        )
    try:
        count = restore_snapshot(vault_path, passphrase, snapshot_id)
        record_event(vault_path, "snapshot_restore", {"snapshot_id": snapshot_id, "var_count": count})
        click.echo(f"Restored {count} variable(s) from snapshot {snapshot_id}.")
    except SnapshotError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
