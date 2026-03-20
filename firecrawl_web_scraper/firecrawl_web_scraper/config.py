"""Configuration helpers for Firecrawl access."""

from __future__ import annotations

import os

FIRECRAWL_SEARCH_URL = "https://api.firecrawl.dev/v2/search"
DEFAULT_TIMEOUT_SECONDS = 15.0


def get_firecrawl_api_key() -> str:
    """Read the Firecrawl API key from the environment."""
    return os.getenv("FIRECRAWL_API_KEY", "").strip()
