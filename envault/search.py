"""Search and filter vault variables by key pattern, value pattern, or tags."""

from __future__ import annotations

import fnmatch
import re
from typing import Dict, List, Optional


class SearchResult:
    """Represents a single search match."""

    def __init__(self, key: str, value: str, matched_on: str) -> None:
        self.key = key
        self.value = value
        self.matched_on = matched_on  # 'key', 'value', or 'tag'

    def __repr__(self) -> str:  # pragma: no cover
        return f"SearchResult(key={self.key!r}, matched_on={self.matched_on!r})"


def search_by_key(
    variables: Dict[str, str],
    pattern: str,
    *,
    use_regex: bool = False,
) -> List[SearchResult]:
    """Return variables whose keys match *pattern*.

    Args:
        variables: Mapping of env var names to values.
        pattern: Glob pattern (default) or regular expression.
        use_regex: When True, treat *pattern* as a regex.
    """
    results: List[SearchResult] = []
    for key, value in variables.items():
        matched = (
            bool(re.search(pattern, key))
            if use_regex
            else fnmatch.fnmatch(key, pattern)
        )
        if matched:
            results.append(SearchResult(key=key, value=value, matched_on="key"))
    return results


def search_by_value(
    variables: Dict[str, str],
    pattern: str,
    *,
    use_regex: bool = False,
) -> List[SearchResult]:
    """Return variables whose values contain *pattern*.

    Args:
        variables: Mapping of env var names to values.
        pattern: Substring (default) or regular expression.
        use_regex: When True, treat *pattern* as a regex.
    """
    results: List[SearchResult] = []
    for key, value in variables.items():
        matched = (
            bool(re.search(pattern, value))
            if use_regex
            else pattern in value
        )
        if matched:
            results.append(SearchResult(key=key, value=value, matched_on="value"))
    return results


def search_by_tag(
    variables: Dict[str, str],
    tag: str,
    tags_meta: Optional[Dict[str, List[str]]] = None,
) -> List[SearchResult]:
    """Return variables that carry *tag* according to *tags_meta*.

    Args:
        variables: Mapping of env var names to values.
        tag: Tag string to look for.
        tags_meta: Mapping of key -> list-of-tags (as stored in vault metadata).
    """
    if not tags_meta:
        return []
    results: List[SearchResult] = []
    for key, value in variables.items():
        if tag in tags_meta.get(key, []):
            results.append(SearchResult(key=key, value=value, matched_on="tag"))
    return results
