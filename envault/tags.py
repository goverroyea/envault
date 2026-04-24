"""Tag management for vault variables."""
from __future__ import annotations

from typing import Dict, List, Optional

TAGS_KEY = "__tags__"


def get_tags(variables: Dict[str, str], key: str) -> List[str]:
    """Return the list of tags for a given variable key."""
    raw = variables.get(TAGS_KEY, "")
    tag_map = _parse_tag_map(raw)
    return tag_map.get(key, [])


def set_tags(variables: Dict[str, str], key: str, tags: List[str]) -> Dict[str, str]:
    """Set tags for a variable key, returning the updated variables dict."""
    raw = variables.get(TAGS_KEY, "")
    tag_map = _parse_tag_map(raw)
    tag_map[key] = sorted(set(tags))
    updated = dict(variables)
    updated[TAGS_KEY] = _serialize_tag_map(tag_map)
    return updated


def remove_tags(variables: Dict[str, str], key: str) -> Dict[str, str]:
    """Remove all tags for a variable key."""
    raw = variables.get(TAGS_KEY, "")
    tag_map = _parse_tag_map(raw)
    tag_map.pop(key, None)
    updated = dict(variables)
    if tag_map:
        updated[TAGS_KEY] = _serialize_tag_map(tag_map)
    else:
        updated.pop(TAGS_KEY, None)
    return updated


def filter_by_tag(variables: Dict[str, str], tag: str) -> Dict[str, str]:
    """Return variables (excluding the tags meta-key) that have the given tag."""
    raw = variables.get(TAGS_KEY, "")
    tag_map = _parse_tag_map(raw)
    return {
        k: v
        for k, v in variables.items()
        if k != TAGS_KEY and tag in tag_map.get(k, [])
    }


def list_all_tags(variables: Dict[str, str]) -> List[str]:
    """Return a sorted list of all unique tags used across all variables."""
    raw = variables.get(TAGS_KEY, "")
    tag_map = _parse_tag_map(raw)
    all_tags: set = set()
    for tags in tag_map.values():
        all_tags.update(tags)
    return sorted(all_tags)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_tag_map(raw: str) -> Dict[str, List[str]]:
    """Parse the compact tag-map string stored inside the vault."""
    result: Dict[str, List[str]] = {}
    if not raw:
        return result
    for entry in raw.split(";"):
        if ":" not in entry:
            continue
        var_key, tags_part = entry.split(":", 1)
        result[var_key] = [t for t in tags_part.split(",") if t]
    return result


def _serialize_tag_map(tag_map: Dict[str, List[str]]) -> str:
    """Serialize the tag map back to the compact string format."""
    parts = []
    for var_key, tags in sorted(tag_map.items()):
        if tags:
            parts.append(f"{var_key}:{','.join(sorted(tags))}")
    return ";".join(parts)
