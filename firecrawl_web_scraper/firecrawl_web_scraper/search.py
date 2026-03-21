"""Public Firecrawl search entrypoint for xFloor fallback retrieval."""

from __future__ import annotations

import importlib
import logging
from typing import Any

from .config import DEFAULT_TIMEOUT_SECONDS, get_firecrawl_api_key
from .normalizer import normalize_firecrawl_response
from .query_builder import build_search_query

logger = logging.getLogger(__name__)


def _build_error_response(*, query_used: str, message: str) -> dict[str, Any]:
    return {
        "status": "error",
        "query_used": query_used,
        "results": [],
        "web": [],
        "news": [],
        "images": [],
        "error": message,
    }


def _load_firecrawl_sdk() -> Any:
    """Load the Firecrawl SDK lazily so tests can stub it easily."""
    return importlib.import_module("firecrawl")


def _perform_search_request(*, api_key: str, payload: dict[str, Any]) -> Any:
    firecrawl_sdk = _load_firecrawl_sdk()
    client = firecrawl_sdk.Firecrawl(api_key=api_key)
    return client.search(**payload)


def call_web_scraper(params: dict, *, limit: int = 5) -> dict[str, Any]:
    """Search Firecrawl and return a stable normalized response for xFloor fallback use.

    The function is intentionally defensive: it never raises raw exceptions to the caller.
    """
    try:
        safe_limit = max(1, min(int(limit), 10))
    except (TypeError, ValueError):
        safe_limit = 5

    plan = build_search_query(params or {})
    query_used = plan.query

    if not query_used:
        return _build_error_response(query_used=query_used, message="Missing search text in params['text'].")

    api_key = get_firecrawl_api_key()
    if not api_key:
        return _build_error_response(query_used=query_used, message="FIRECRAWL_API_KEY is not configured.")

    payload: dict[str, Any] = {
        "query": query_used,
        "limit": safe_limit,
        "sources": ["web", "images", "news"],
    }
    if plan.categories:
        payload["categories"] = plan.categories
    if plan.tbs:
        payload["tbs"] = plan.tbs
    payload["timeout"] = int(DEFAULT_TIMEOUT_SECONDS * 1000)

    try:
        logger.info("Running Firecrawl search", extra={"query": query_used, "limit": safe_limit})
        raw_response = _perform_search_request(api_key=api_key, payload=payload)
        normalized = normalize_firecrawl_response(raw_response, query_used=query_used, limit=safe_limit)
        if normalized["status"] == "error":
            logger.warning("Firecrawl search returned no usable results", extra={"query": query_used})
        return normalized
    except ModuleNotFoundError:
        return _build_error_response(
            query_used=query_used,
            message="firecrawl-py is not installed. Run `poetry install` before using this helper.",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected web scraper failure: %s", exc)
        return _build_error_response(query_used=query_used, message="Unexpected error while searching the web.")
