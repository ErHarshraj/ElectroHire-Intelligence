from datetime import datetime, timezone

from packages.opportunity.company_identifier import CompanyIdentifier
from packages.opportunity.discovery import StartupNewsItem


def make_item(title: str) -> StartupNewsItem:
    return StartupNewsItem(
        title=title,
        summary=None,
        url="https://example.com/article",
        published_at=datetime.now(timezone.utc),
        source_name="Test Source",
        query="startup",
    )


def test_extracts_company_from_raises_title() -> None:
    identifier = CompanyIdentifier()

    result = identifier.identify(
        make_item("Yaanendriya raises ₹15 crore for robotics expansion")
    )

    assert result.company is not None
    assert result.company.name == "Yaanendriya"
    assert result.confidence == "MEDIUM"


def test_extracts_company_from_launch_title() -> None:
    identifier = CompanyIdentifier()

    result = identifier.identify(
        make_item("Automind Dynamics launches new robotics platform")
    )

    assert result.company is not None
    assert result.company.name == "Automind Dynamics"


def test_extracts_company_from_secures_title() -> None:
    identifier = CompanyIdentifier()

    result = identifier.identify(
        make_item("Example Technologies secures fresh funding")
    )

    assert result.company is not None
    assert result.company.name == "Example Technologies"


def test_removes_legal_suffix() -> None:
    identifier = CompanyIdentifier()

    result = identifier.identify(
        make_item("Example Electronics Private Limited launches new product")
    )

    assert result.company is not None
    assert result.company.name == "Example Electronics"


def test_removes_india_prefix() -> None:
    identifier = CompanyIdentifier()

    result = identifier.identify(
        make_item("India: Example Robotics raises funding")
    )

    assert result.company is not None
    assert result.company.name == "Example Robotics"


def test_rejects_generic_startup_title() -> None:
    identifier = CompanyIdentifier()

    result = identifier.identify(
        make_item("Indian startup raises ₹20 crore")
    )

    assert result.company is None
    assert result.confidence == "NONE"


def test_rejects_title_without_company_action_pattern() -> None:
    identifier = CompanyIdentifier()

    result = identifier.identify(
        make_item("New robotics technology could transform warehouses")
    )

    assert result.company is None


def test_rejects_empty_title() -> None:
    identifier = CompanyIdentifier()

    result = identifier.identify(make_item(""))

    assert result.company is None
