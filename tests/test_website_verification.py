import httpx

from packages.opportunity.models import Company
from packages.opportunity.website_verification import (
    CompanyWebsiteVerifier,
)


def make_client(html: str, status_code: int = 200) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code,
            text=html,
            request=request,
        )

    return httpx.Client(
        transport=httpx.MockTransport(handler),
    )


def make_company() -> Company:
    return Company(
        name="Yaanendriya",
        industry="Robotics",
        stage="Startup",
        signals=("robotics", "hardware"),
    )


def test_verifies_company_when_name_is_in_title() -> None:
    verifier = CompanyWebsiteVerifier(
        client=make_client(
            "<html><head><title>Yaanendriya | Robotics</title></head></html>"
        )
    )

    result = verifier.verify(
        make_company(),
        "https://yaanendriya.example",
    )

    assert result.verified is True
    assert result.confidence == "HIGH"
    assert result.company.website == "https://yaanendriya.example"
    assert result.website == "https://yaanendriya.example"


def test_verifies_company_when_name_is_in_page_content() -> None:
    verifier = CompanyWebsiteVerifier(
        client=make_client(
            "<html><body><h1>About Yaanendriya</h1></body></html>"
        )
    )

    result = verifier.verify(
        make_company(),
        "https://example.com/company",
    )

    assert result.verified is True
    assert result.confidence == "HIGH"


def test_reachable_unrelated_website_is_not_verified() -> None:
    verifier = CompanyWebsiteVerifier(
        client=make_client(
            "<html><head><title>Example Robotics</title></head></html>"
        )
    )

    result = verifier.verify(
        make_company(),
        "https://example.com",
    )

    assert result.verified is False
    assert result.confidence == "LOW"
    assert result.company.website == "https://example.com"


def test_normalizes_missing_scheme() -> None:
    verifier = CompanyWebsiteVerifier(
        client=make_client(
            "<html><title>Yaanendriya</title></html>"
        )
    )

    result = verifier.verify(
        make_company(),
        "yaanendriya.example/",
    )

    assert result.verified is True
    assert result.website == "https://yaanendriya.example"


def test_rejects_empty_url_without_network_request() -> None:
    verifier = CompanyWebsiteVerifier(
        client=make_client(
            "<html><title>Yaanendriya</title></html>"
        )
    )

    result = verifier.verify(
        make_company(),
        "",
    )

    assert result.verified is False
    assert result.confidence == "NONE"


def test_handles_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            text="Not Found",
            request=request,
        )

    verifier = CompanyWebsiteVerifier(
        client=httpx.Client(
            transport=httpx.MockTransport(handler),
        )
    )

    result = verifier.verify(
        make_company(),
        "https://example.com",
    )

    assert result.verified is False
    assert result.confidence == "NONE"


def test_preserves_existing_company_metadata() -> None:
    company = Company(
        name="Yaanendriya",
        location="Bengaluru",
        industry="Robotics",
        founded_year=2024,
        stage="Seed",
        size="11-50",
        signals=("robotics", "sensors"),
    )

    verifier = CompanyWebsiteVerifier(
        client=make_client(
            "<html><title>Yaanendriya</title></html>"
        )
    )

    result = verifier.verify(
        company,
        "https://example.com",
    )

    assert result.company.location == "Bengaluru"
    assert result.company.industry == "Robotics"
    assert result.company.founded_year == 2024
    assert result.company.stage == "Seed"
    assert result.company.size == "11-50"
    assert result.company.signals == ("robotics", "sensors")


def test_timeout_validation() -> None:
    try:
        CompanyWebsiteVerifier(timeout=0)
    except ValueError as exc:
        assert "greater than zero" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
