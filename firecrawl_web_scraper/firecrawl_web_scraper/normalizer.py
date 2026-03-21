"""Normalize Firecrawl search responses into the xFloor fallback contract."""

from __future__ import annotations

from .utils import first_non_empty, truncate_text, unique_strings, url_host


def _to_plain_data(value):
    """Recursively coerce SDK response objects into plain Python data structures."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {key: _to_plain_data(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_plain_data(item) for item in value]

    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return _to_plain_data(model_dump())

    dict_method = getattr(value, "dict", None)
    if callable(dict_method):
        return _to_plain_data(dict_method())

    object_dict = getattr(value, "__dict__", None)
    if isinstance(object_dict, dict) and object_dict:
        return {key: _to_plain_data(item) for key, item in object_dict.items() if not key.startswith("_")}

    return value


def _extract_media(item: dict, image_lookup: dict[str, list[str]]) -> list[str]:
    direct_media = unique_strings(
        [
            item.get("image"),
            item.get("imageUrl"),
            item.get("thumbnail"),
            item.get("video"),
            item.get("videoUrl"),
            item.get("ogImage"),
            item.get("favicon"),
        ]
    )
    page_url = item.get("url") or item.get("sourceURL") or item.get("sourceUrl")
    if not page_url:
        return direct_media
    return unique_strings(direct_media + image_lookup.get(page_url, []) + image_lookup.get(url_host(page_url), []))


def _build_image_lookup(images: list[dict] | None) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for image in images or []:
        candidates = unique_strings(
            [
                image.get("url"),
                image.get("imageUrl"),
                image.get("src"),
                image.get("thumbnail"),
            ]
        )
        if not candidates:
            continue
        for key in unique_strings(
            [
                image.get("sourceURL"),
                image.get("sourceUrl"),
                image.get("pageURL"),
                image.get("pageUrl"),
                url_host(image.get("sourceURL") or image.get("pageURL") or image.get("url")),
            ]
        ):
            lookup.setdefault(key, [])
            lookup[key] = unique_strings(lookup[key] + candidates)
    return lookup


def _derive_summary(item: dict) -> str:
    metadata = item.get("metadata") or {}
    return truncate_text(
        first_non_empty(
            item.get("summary"),
            item.get("description"),
            item.get("snippet"),
            item.get("markdown"),
            metadata.get("description"),
            metadata.get("ogDescription"),
        ),
        max_length=320,
    )


def _extract_result_buckets(payload: dict) -> tuple[bool, dict]:
    """Extract Firecrawl result buckets from the supported response shapes."""
    payload = _to_plain_data(payload)
    if not isinstance(payload, dict):
        return False, {}

    success = payload.get("success")
    if success is None:
        status = payload.get("status")
        success = True if status == "success" else None if status is None else False
    if success is None and any(key in payload for key in ("web", "news", "images")):
        success = True

    if not success:
        return False, {}

    data = payload.get("data")
    if isinstance(data, dict):
        return True, data
    if isinstance(data, list):
        return True, {"web": data, "news": [], "images": []}
    if any(key in payload for key in ("web", "news", "images")):
        return True, {
            "web": payload.get("web") or [],
            "news": payload.get("news") or [],
            "images": payload.get("images") or [],
        }
    return True, {}


def normalize_firecrawl_response(payload: dict, *, query_used: str, limit: int) -> dict:
    """Normalize a Firecrawl response into the stable helper contract."""
    success, data = _extract_result_buckets(payload)
    if not success:
        return {
            "status": "error",
            "query_used": query_used,
            "results": [],
            "error": "Firecrawl search was unsuccessful.",
        }
    if not isinstance(data, dict):
        return {
            "status": "error",
            "query_used": query_used,
            "results": [],
            "error": "Firecrawl response was malformed.",
        }

    image_lookup = _build_image_lookup(data.get("images"))
    merged_items = []
    seen_urls: set[str] = set()

    for bucket_name in ("web", "news"):
        for item in data.get(bucket_name) or []:
            url = first_non_empty(item.get("url"), item.get("sourceURL"), item.get("sourceUrl"))
            title = first_non_empty(item.get("title"), item.get("metadata", {}).get("title"))
            description = truncate_text(
                first_non_empty(
                    item.get("description"),
                    item.get("snippet"),
                    item.get("metadata", {}).get("description"),
                ),
                max_length=240,
            )
            summary = _derive_summary(item)

            if not url or url in seen_urls or not (title or description or summary):
                continue

            seen_urls.add(url)
            merged_items.append(
                {
                    "title": title,
                    "description": description,
                    "url": url,
                    "media": _extract_media(item, image_lookup),
                    "summary": summary,
                }
            )
            if len(merged_items) >= limit:
                break
        if len(merged_items) >= limit:
            break

    if not merged_items:
        return {
            "status": "error",
            "query_used": query_used,
            "results": [],
            "error": "Firecrawl returned no usable results.",
        }

    return {
        "status": "success",
        "query_used": query_used,
        "results": merged_items,
        "error": None,
    }
