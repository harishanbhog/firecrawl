from firecrawl_web_scraper.search import call_web_scraper


class _MockResponse:
    def __init__(self, payload: dict):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _MockClient:
    def __init__(self, *args, **kwargs):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, headers=None, json=None):
        self.calls.append({"url": url, "headers": headers, "json": json})
        return _MockResponse(
            {
                "success": True,
                "data": {
                    "web": [
                        {
                            "title": "RVCE Events",
                            "description": "Campus event list",
                            "url": "https://rvce.edu/events",
                            "summary": "Today there is a workshop on campus.",
                        }
                    ]
                },
            }
        )


class _MockHttpxModule:
    Client = _MockClient

    class HTTPError(Exception):
        pass

    class HTTPStatusError(HTTPError):
        def __init__(self, response):
            self.response = response


def test_call_web_scraper_returns_normalized_success(monkeypatch) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    monkeypatch.setattr("firecrawl_web_scraper.search._load_httpx", lambda: _MockHttpxModule)

    result = call_web_scraper(
        {
            "text": "Any events happening today",
            "topic": "RVCE",
            "floor_title": "RV College Of Engineering",
            "floor_desc": "An autonomous engineering college in Bengaluru",
        },
        limit=3,
    )

    assert result["status"] == "success"
    assert result["error"] is None
    assert result["results"][0]["url"] == "https://rvce.edu/events"
    assert "RV College Of Engineering" in result["query_used"]


def test_call_web_scraper_handles_missing_api_key(monkeypatch) -> None:
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)

    result = call_web_scraper({"text": "latest notices"})

    assert result == {
        "status": "error",
        "query_used": "latest notices",
        "results": [],
        "error": "FIRECRAWL_API_KEY is not configured.",
    }
