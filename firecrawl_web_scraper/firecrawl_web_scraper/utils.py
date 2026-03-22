"""Shared utility helpers for query construction and response normalization."""

from __future__ import annotations

import re
from urllib.parse import urlparse

_WHITESPACE_RE = re.compile(r"\s+")


def compact_text(value: str | None) -> str:
    """Collapse whitespace and strip a text value."""
    if not value:
        return ""
    return _WHITESPACE_RE.sub(" ", value).strip()


def truncate_text(value: str | None, *, max_length: int = 280) -> str:
    """Return a trimmed string that does not exceed max_length characters."""
    text = compact_text(value)
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "…"


def first_non_empty(*values: str | None) -> str:
    """Return the first non-empty text candidate."""
    for value in values:
        text = compact_text(value)
        if text:
            return text
    return ""


def unique_strings(values: list[str | None]) -> list[str]:
    """Return de-duplicated non-empty string values while preserving order."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = compact_text(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def url_host(url: str | None) -> str:
    """Extract a normalized host name from a URL."""
    if not url:
        return ""
    try:
        return urlparse(url).netloc.lower()
    except ValueError:
        return ""
