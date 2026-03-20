"""Lightweight internal models used by the Firecrawl search helper."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class QueryPlan:
    """Represents the Firecrawl query strategy derived from input params."""

    query: str
    categories: list[str] = field(default_factory=list)
    tbs: str | None = None
