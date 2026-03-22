"""Deterministic logic for building a context-aware Firecrawl query."""

from __future__ import annotations

from .models import QueryPlan
from .utils import compact_text, unique_strings

_GITHUB_HINTS = {
    "github",
    "gitlab",
    "repo",
    "repository",
    "repositories",
    "open source",
    "opensource",
    "source code",
    "code example",
    "code examples",
    "sample code",
    "project ideas",
    "student ai projects",
    "implementation",
    "sdk",
    "library",
}

_DAILY_HINTS = {"today", "breaking", "right now"}
_WEEKLY_HINTS = {"this week", "weekly"}
_RECENT_HINTS = {"recent", "latest", "new", "newest", "updated"}


def infer_categories(text: str) -> list[str]:
    """Infer Firecrawl categories from the user's query."""
    normalized = compact_text(text).lower()
    if any(hint in normalized for hint in _GITHUB_HINTS):
        return ["github"]
    return []


def infer_tbs(text: str) -> str | None:
    """Infer a recency hint for time-sensitive queries."""
    normalized = compact_text(text).lower()
    if any(hint in normalized for hint in _DAILY_HINTS):
        return "qdr:d"
    if any(hint in normalized for hint in _WEEKLY_HINTS):
        return "qdr:w"
    if any(hint in normalized for hint in _RECENT_HINTS):
        return "qdr:m"
    return None


def build_search_query(params: dict) -> QueryPlan:
    """Build a concise Firecrawl query enriched with floor context when helpful."""
    text = compact_text(params.get("text"))
    topic = compact_text(params.get("topic"))
    floor_title = compact_text(params.get("floor_title"))
    floor_desc = compact_text(params.get("floor_desc"))

    if not text:
        return QueryPlan(query="")

    context_bits = unique_strings([floor_title, topic])
    query = text

    if context_bits:
        query = f"{text} for {' '.join(context_bits)}"

    if floor_desc:
        query = f"{query} ({floor_desc})"

    return QueryPlan(
        query=query,
        categories=infer_categories(text),
        tbs=infer_tbs(text),
    )
