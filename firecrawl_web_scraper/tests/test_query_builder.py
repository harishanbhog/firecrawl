from firecrawl_web_scraper.query_builder import build_search_query


def test_build_search_query_enriches_with_floor_context() -> None:
    plan = build_search_query(
        {
            "text": "Any events happening today",
            "topic": "RVCE",
            "floor_title": "RV College Of Engineering",
            "floor_desc": "An autonomous engineering college in Bengaluru",
        }
    )

    assert plan.query == (
        "Any events happening today for RV College Of Engineering RVCE "
        "(An autonomous engineering college in Bengaluru)"
    )
    assert plan.tbs == "qdr:d"
    assert plan.categories == []


def test_build_search_query_detects_github_intent() -> None:
    plan = build_search_query(
        {
            "text": "Show open source repo ideas and GitHub code examples",
            "topic": "AI Club",
        }
    )

    assert plan.categories == ["github"]
    assert plan.query == "Show open source repo ideas and GitHub code examples for AI Club"
