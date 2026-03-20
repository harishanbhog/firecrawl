from firecrawl_web_scraper.normalizer import normalize_firecrawl_response


def test_normalize_firecrawl_response_merges_and_deduplicates_results() -> None:
    payload = {
        "success": True,
        "data": {
            "web": [
                {
                    "title": "Main Result",
                    "description": "Primary description",
                    "url": "https://example.edu/events",
                    "summary": "Detailed result summary",
                },
                {
                    "title": "Duplicate Result",
                    "description": "Should be skipped",
                    "url": "https://example.edu/events",
                },
            ],
            "news": [
                {
                    "title": "News Result",
                    "snippet": "Recent update",
                    "url": "https://news.example.edu/post",
                    "metadata": {"description": "News metadata description"},
                }
            ],
            "images": [
                {
                    "sourceURL": "https://example.edu/events",
                    "imageUrl": "https://cdn.example.edu/event.jpg",
                }
            ],
        },
    }

    normalized = normalize_firecrawl_response(payload, query_used="events rvce", limit=5)

    assert normalized["status"] == "success"
    assert normalized["error"] is None
    assert [item["url"] for item in normalized["results"]] == [
        "https://example.edu/events",
        "https://news.example.edu/post",
    ]
    assert normalized["results"][0]["media"] == ["https://cdn.example.edu/event.jpg"]
    assert normalized["results"][1]["summary"] == "Recent update"


def test_normalize_firecrawl_response_errors_on_empty_results() -> None:
    normalized = normalize_firecrawl_response({"success": True, "data": {}}, query_used="q", limit=3)

    assert normalized == {
        "status": "error",
        "query_used": "q",
        "results": [],
        "error": "Firecrawl returned no usable results.",
    }
