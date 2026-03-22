"""Local demo script for trying the Firecrawl helper manually."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from firecrawl_web_scraper.search import call_web_scraper


if __name__ == "__main__":
    params = {
        "floor_id": "1349864942665",
        "text": "Any events happening today",
        "topic": "RVCE",
        "floor_title": "RV College Of Engineering",
        "floor_desc": "An autonomous engineering college in Bengaluru",
    }
    result = call_web_scraper(params, limit=5)
    print(json.dumps(result, indent=2))
