from datetime import datetime, timezone

from packages.opportunity.company_verification import (
    CompanyVerificationEngine,
)
from packages.opportunity.discovery import StartupNewsItem


def make_item(
    title: str,
    url: str,
    source_name: str,
) -> StartupNewsItem:
    return StartupNewsItem(
        title=title,
        summary=None,
        url=url,
        published_at=datetime.now(timezone.utc),
        source_name=source_name,
        query="startup",
    )


def test_single_article_has_low_confidence() -> None:
    engine = CompanyVerificationEngine()

    result = engine.verify(
        [
            make_item(
                "Yaanendriya raises funding",
                "https://example.com/article-1",
                "Example News",
            )
        ]
    )

    assert len(result) == 1
    assert result[0].company is not None
    assert result[0].company.name == "Yaanendriya"
    assert result[0].confidence == "LOW"
    assert result[0].article_count == 1
    assert result[0].source_count == 1


def test_multiple_articles_from_same_source_have_medium_confidence() -> None:
    engine = CompanyVerificationEngine()

    result = engine.verify(
        [
            make_item(
                "Yaanendriya raises funding",
                "https://example.com/article-1",
                "Example News",
            ),
            make_item(
                "Yaanendriya expands robotics development",
                "https://example.com/article-2",
                "Example News",
            ),
        ]
    )

    assert len(result) == 1
    assert result[0].confidence == "MEDIUM"
    assert result[0].article_count == 2
    assert result[0].source_count == 1


def test_multiple_articles_from_multiple_sources_have_high_confidence() -> None:
    engine = CompanyVerificationEngine()

    result = engine.verify(
        [
            make_item(
                "Yaanendriya raises funding",
                "https://example.com/article-1",
                "Example News",
            ),
            make_item(
                "Yaanendriya expands robotics development",
                "https://another.example/article-2",
                "Another News",
            ),
        ]
    )

    assert len(result) == 1
    assert result[0].confidence == "HIGH"
    assert result[0].article_count == 2
    assert result[0].source_count == 2


def test_duplicate_article_url_is_not_counted_twice() -> None:
    engine = CompanyVerificationEngine()

    result = engine.verify(
        [
            make_item(
                "Yaanendriya raises funding",
                "https://example.com/article-1",
                "Example News",
            ),
            make_item(
                "Yaanendriya raises funding",
                "https://example.com/article-1",
                "Example News",
            ),
        ]
    )

    assert len(result) == 1
    assert result[0].confidence == "LOW"
    assert result[0].article_count == 1


def test_company_names_are_grouped_case_insensitively() -> None:
    engine = CompanyVerificationEngine()

    result = engine.verify(
        [
            make_item(
                "Yaanendriya raises funding",
                "https://example.com/article-1",
                "Example News",
            ),
            make_item(
                "YAANENDRIYA launches robotics product",
                "https://another.example/article-2",
                "Another News",
            ),
        ]
    )

    assert len(result) == 1
    assert result[0].company is not None
    assert result[0].company.name == "Yaanendriya"
    assert result[0].article_count == 2


def test_unidentified_companies_are_ignored() -> None:
    engine = CompanyVerificationEngine()

    result = engine.verify(
        [
            make_item(
                "New robotics technology could transform warehouses",
                "https://example.com/article-1",
                "Example News",
            )
        ]
    )

    assert result == []


def test_multiple_companies_are_returned_separately() -> None:
    engine = CompanyVerificationEngine()

    result = engine.verify(
        [
            make_item(
                "Yaanendriya raises funding",
                "https://example.com/article-1",
                "Example News",
            ),
            make_item(
                "Automind Dynamics launches robotics platform",
                "https://example.com/article-2",
                "Example News",
            ),
        ]
    )

    assert len(result) == 2
    assert {item.company.name for item in result if item.company} == {
        "Yaanendriya",
        "Automind Dynamics",
    }


def test_results_are_ranked_by_confidence() -> None:
    engine = CompanyVerificationEngine()

    result = engine.verify(
        [
            make_item(
                "Yaanendriya raises funding",
                "https://example.com/article-1",
                "Example News",
            ),
            make_item(
                "Yaanendriya expands robotics development",
                "https://another.example/article-2",
                "Another News",
            ),
            make_item(
                "Automind Dynamics launches robotics platform",
                "https://example.com/article-3",
                "Example News",
            ),
        ]
    )

    assert result[0].company is not None
    assert result[0].company.name == "Yaanendriya"
    assert result[0].confidence == "HIGH"
