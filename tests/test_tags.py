"""Tests for envault.tags and the tags CLI commands."""
import pytest
from click.testing import CliRunner

from envault.tags import (
    get_tags,
    set_tags,
    remove_tags,
    filter_by_tag,
    list_all_tags,
    TAGS_KEY,
)


# ---------------------------------------------------------------------------
# Unit tests for tags.py
# ---------------------------------------------------------------------------

def test_get_tags_empty_when_no_meta():
    variables = {"FOO": "bar"}
    assert get_tags(variables, "FOO") == []


def test_set_tags_stores_tags():
    variables = {"FOO": "bar"}
    updated = set_tags(variables, "FOO", ["prod", "secret"])
    assert "prod" in get_tags(updated, "FOO")
    assert "secret" in get_tags(updated, "FOO")


def test_set_tags_deduplicates():
    variables = {"FOO": "bar"}
    updated = set_tags(variables, "FOO", ["prod", "prod", "dev"])
    assert get_tags(updated, "FOO").count("prod") == 1


def test_set_tags_does_not_mutate_original():
    variables = {"FOO": "bar"}
    set_tags(variables, "FOO", ["prod"])
    assert TAGS_KEY not in variables


def test_remove_tags_clears_entry():
    variables = {"FOO": "bar"}
    with_tags = set_tags(variables, "FOO", ["prod"])
    without = remove_tags(with_tags, "FOO")
    assert get_tags(without, "FOO") == []
    assert TAGS_KEY not in without


def test_remove_tags_keeps_other_keys():
    variables = {"FOO": "bar", "BAZ": "qux"}
    with_tags = set_tags(variables, "FOO", ["prod"])
    with_tags = set_tags(with_tags, "BAZ", ["dev"])
    without = remove_tags(with_tags, "FOO")
    assert get_tags(without, "BAZ") == ["dev"]


def test_filter_by_tag_returns_matching():
    variables = {"FOO": "1", "BAR": "2", "BAZ": "3"}
    v = set_tags(variables, "FOO", ["prod"])
    v = set_tags(v, "BAR", ["prod", "dev"])
    v = set_tags(v, "BAZ", ["dev"])
    result = filter_by_tag(v, "prod")
    assert set(result.keys()) == {"FOO", "BAR"}


def test_filter_by_tag_excludes_tags_meta_key():
    variables = {"FOO": "1"}
    v = set_tags(variables, "FOO", ["prod"])
    result = filter_by_tag(v, "prod")
    assert TAGS_KEY not in result


def test_list_all_tags_returns_sorted_unique():
    variables = {"A": "1", "B": "2"}
    v = set_tags(variables, "A", ["prod", "secret"])
    v = set_tags(v, "B", ["dev", "prod"])
    all_tags = list_all_tags(v)
    assert all_tags == ["dev", "prod", "secret"]


def test_list_all_tags_empty_when_none():
    assert list_all_tags({"FOO": "bar"}) == []


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def vault_path(tmp_path, runner):
    from envault.cli import cli
    path = str(tmp_path / "vault.env")
    runner.invoke(cli, ["set", "FOO", "bar", "--vault", path, "--passphrase", "pw"])
    runner.invoke(cli, ["set", "BAR", "baz", "--vault", path, "--passphrase", "pw"])
    return path


def test_cli_set_tag(runner, vault_path):
    from envault.cli_tags import tags_group
    result = runner.invoke(
        tags_group,
        ["set", "FOO", "prod", "--vault", vault_path, "--passphrase", "pw"],
    )
    assert result.exit_code == 0
    assert "prod" in result.output


def test_cli_list_tags_for_key(runner, vault_path):
    from envault.cli_tags import tags_group
    runner.invoke(tags_group, ["set", "FOO", "prod", "--vault", vault_path, "--passphrase", "pw"])
    result = runner.invoke(tags_group, ["list", "FOO", "--vault", vault_path, "--passphrase", "pw"])
    assert result.exit_code == 0
    assert "prod" in result.output


def test_cli_filter_tag(runner, vault_path):
    from envault.cli_tags import tags_group
    runner.invoke(tags_group, ["set", "FOO", "prod", "--vault", vault_path, "--passphrase", "pw"])
    result = runner.invoke(tags_group, ["filter", "prod", "--vault", vault_path, "--passphrase", "pw"])
    assert result.exit_code == 0
    assert "FOO" in result.output


def test_cli_set_tag_missing_key_exits_nonzero(runner, vault_path):
    from envault.cli_tags import tags_group
    result = runner.invoke(
        tags_group,
        ["set", "MISSING", "prod", "--vault", vault_path, "--passphrase", "pw"],
    )
    assert result.exit_code != 0
