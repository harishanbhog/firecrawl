# Firecrawl Web Scraper Helper

A small standalone Poetry project that wraps the official Firecrawl Python SDK behind a stable Python function for xFloor's web-search fallback flow.

## Public API

```python
from firecrawl_web_scraper.search import call_web_scraper

result = call_web_scraper(params, limit=5)
```

The function always returns a normalized JSON-like dictionary shaped for xFloor fallback usage:

```python
{
    "status": "success" | "error",
    "query_used": "...",
    "results": [
        {
            "title": "...",
            "description": "...",
            "url": "...",
            "media": ["..."],
            "summary": "...",
        }
    ],
    "error": None | "human readable message",
}
```

## Project layout

```text
firecrawl_web_scraper/
  pyproject.toml
  README.md
  .env.example
  firecrawl_web_scraper/
    __init__.py
    config.py
    models.py
    normalizer.py
    query_builder.py
    search.py
    utils.py
  scripts/
    demo_search.py
  tests/
    test_normalizer.py
    test_query_builder.py
    test_search_smoke.py
```

## Setup

1. Ensure you have Python 3.11+ and Poetry installed.
2. Enter the project directory:

   ```bash
   cd firecrawl_web_scraper
   ```

3. Install dependencies:

   ```bash
   poetry install
   ```

4. Configure the Firecrawl API key:

   ```bash
   cp .env.example .env
   export FIRECRAWL_API_KEY=your_firecrawl_api_key_here
   ```

## Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `FIRECRAWL_API_KEY` | Yes | API key used by the official Firecrawl Python SDK. |

## Query-building behavior

The helper builds a deterministic, context-aware Firecrawl query by:

- starting from `params["text"]`,
- appending `floor_title` and `topic` only when present,
- adding `floor_desc` in a concise parenthetical when available,
- inferring GitHub intent from terms like `github`, `repo`, `open source`, or `code examples`,
- inferring a time-sensitive `tbs` hint for queries that mention terms such as `today`, `latest`, or `this week`.

The helper uses the official Python SDK pattern:

```python
from firecrawl import Firecrawl

firecrawl = Firecrawl(api_key="fc-YOUR-API-KEY")
results = firecrawl.search(query="firecrawl", limit=3)
```

The request sent through the SDK uses:

- `sources=["web"]`,
- `limit=<function arg>`,
- `categories=["github"]` only when the query implies code/repository intent,
- standard search results by default so the helper preserves the full search result set consistently,
- local summary derivation from the best available Firecrawl fields instead of forcing scraped-content mode on every search,
- a bounded timeout,
- no PDF category.

## Run the demo locally

Once `FIRECRAWL_API_KEY` is set:

```bash
poetry run python scripts/demo_search.py
```

The demo script prints normalized JSON to stdout.

## Run tests

```bash
poetry run pytest
```

## How to plug this into xFloor later

You can copy this folder into the xFloor backend, add it to the Python path, and import it directly:

```python
from firecrawl_web_scraper.search import call_web_scraper

params = {
    "floor_id": "1349864942665",
    "text": "Any events happening today",
    "topic": "RVCE",
    "floor_title": "RV College Of Engineering",
    "floor_desc": "An autonomous engineering college in Bengaluru",
}

data = call_web_scraper(params)

if "error" in data or "results" not in data or data.get("status") != "success":
    # fall back handling
    pass
```

Because `call_web_scraper` is stateless and always returns the same top-level contract, it can be used as a drop-in fallback helper from the main xFloor retrieval code.
