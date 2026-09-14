from __future__ import annotations

import httpx

from packages.opportunity.website_discovery import (
    CompanyWebsiteDiscovery,
)


def make_client(html: str) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            text=html,
            request=request,
        )

    return httpx.Client(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
    )


def test_discovers_company_website_from_link() -> None:
    html = """
    <html>
        <body>
            <a href="https://example.com">Example Robotics</a>
        </body>
    </html>
    """

    discovery = CompanyWebsiteDiscovery(
        client=make_client(html),
    )

    results = discovery.discover_from_page(
        company_name="Example Robotics",
        page_url="https://news.example.org/article",
    )

    assert len(results) == 1
    assert results[0].website == "https://example.com"
    assert results[0].company_name == "Example Robotics"


def test_does_not_guess_company_domain() -> None:
    html = """
    <html>
        <body>
            <p>Example Robotics raised funding.</p>
        </body>
    </html>
    """

    discovery = CompanyWebsiteDiscovery(
        client=make_client(html),
    )

    results = discovery.discover_from_page(
        company_name="Example Robotics",
        page_url="https://news.example.org/article",
    )

    assert results == []


def test_ignores_social_media_links() -> None:
    html = """
    <html>
        <body>
            <a href="https://linkedin.com/company/example-robotics">
                Example Robotics
            </a>
            <a href="https://example.com">
                Example Robotics
            </a>
        </body>
    </html>
    """

    discovery = CompanyWebsiteDiscovery(
        client=make_client(html),
    )

    results = discovery.discover_from_page(
        company_name="Example Robotics",
        page_url="https://news.example.org/article",
    )

    assert len(results) == 1
    assert results[0].website == "https://example.com"


def test_ignores_source_domain() -> None:
    html = """
    <html>
        <body>
            <a href="https://news.example.org/example-robotics">
                Example Robotics
            </a>
        </body>
    </html>
    """

    discovery = CompanyWebsiteDiscovery(
        client=make_client(html),
    )

    results = discovery.discover_from_page(
        company_name="Example Robotics",
        page_url="https://news.example.org/article",
    )

    assert results == []


def test_deduplicates_same_website() -> None:
    html = """
    <html>
        <body>
            <a href="https://example.com">Example Robotics</a>
            <a href="https://example.com/">Example Robotics</a>
        </body>
    </html>
    """

    discovery = CompanyWebsiteDiscovery(
        client=make_client(html),
    )

    results = discovery.discover_from_page(
        company_name="Example Robotics",
        page_url="https://news.example.org/article",
    )

    assert len(results) == 1


def test_invalid_company_name_returns_empty() -> None:
    html = """
    <html>
        <body>
            <a href="https://example.com">Example</a>
        </body>
    </html>
    """

    discovery = CompanyWebsiteDiscovery(
        client=make_client(html),
    )

    results = discovery.discover_from_page(
        company_name="",
        page_url="https://news.example.org/article",
    )

    assert results == []


def test_http_error_returns_empty() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            text="Not Found",
            request=request,
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
    )

    discovery = CompanyWebsiteDiscovery(client=client)

    results = discovery.discover_from_page(
        company_name="Example Robotics",
        page_url="https://news.example.org/article",
    )

    assert results == []
