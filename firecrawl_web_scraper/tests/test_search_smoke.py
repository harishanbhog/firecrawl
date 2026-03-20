from firecrawl_web_scraper.search import call_web_scraper


class _MockFirecrawlClient:
    def __init__(self, *, api_key: str):
        self.api_key = api_key
        self.calls = []

    def search(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "status": "success",
            "web": [
                {
                    "title": "RVCE Events",
                    "description": "Campus event list",
                    "url": "https://rvce.edu/events",
                    "summary": "Today there is a workshop on campus.",
                }
            ],
            "news": [],
            "images": [],
        }


class _MockFirecrawlModule:
    def __init__(self):
        self.instances = []

    def Firecrawl(self, *, api_key: str):
        client = _MockFirecrawlClient(api_key=api_key)
        self.instances.append(client)
        return client


_MOCK_FIRECRAWL_MODULE = _MockFirecrawlModule()


def _load_mock_firecrawl_sdk():
    return _MOCK_FIRECRAWL_MODULE


def test_call_web_scraper_returns_normalized_success(monkeypatch) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    monkeypatch.setattr("firecrawl_web_scraper.search._load_firecrawl_sdk", _load_mock_firecrawl_sdk)

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
    assert _MOCK_FIRECRAWL_MODULE.instances
    client = _MOCK_FIRECRAWL_MODULE.instances[-1]
    assert client.api_key == "test-key"
    assert client.calls[0]["sources"] == ["web"]
    assert client.calls[0]["limit"] == 3
    assert "scrapeOptions" not in client.calls[0]


def test_call_web_scraper_handles_missing_api_key(monkeypatch) -> None:
    monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)

    result = call_web_scraper({"text": "latest notices"})

    assert result == {
        "status": "error",
        "query_used": "latest notices",
        "results": [],
        "error": "FIRECRAWL_API_KEY is not configured.",
    }


def test_call_web_scraper_handles_missing_sdk(monkeypatch) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")

    def _missing_sdk():
        raise ModuleNotFoundError("firecrawl")

    monkeypatch.setattr("firecrawl_web_scraper.search._load_firecrawl_sdk", _missing_sdk)

    result = call_web_scraper({"text": "latest notices"})

    assert result == {
        "status": "error",
        "query_used": "latest notices",
        "results": [],
        "error": "firecrawl-py is not installed. Run `poetry install` before using this helper.",
    }
