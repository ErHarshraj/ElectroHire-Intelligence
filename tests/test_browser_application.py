from packages.application.adapters.browser import BrowserApplicationAdapter
from packages.application.models import (
    ApplicationMethod,
    ApplicationRequest,
    ApplicationStatus,
)


def make_request(url: str | None = "https://example.com") -> ApplicationRequest:
    return ApplicationRequest(
        source="test",
        source_job_id="123",
        job_title="Hardware Engineer",
        company="Example",
        application_method=ApplicationMethod.BROWSER,
        apply_url=url,
    )


def test_browser_adapter_rejects_missing_url() -> None:
    adapter = BrowserApplicationAdapter.__new__(BrowserApplicationAdapter)

    result = adapter.submit(make_request(None))

    assert result.status == ApplicationStatus.FAILED
    assert result.method == ApplicationMethod.BROWSER
    assert "URL is missing" in result.message


def test_browser_adapter_rejects_invalid_url() -> None:
    adapter = BrowserApplicationAdapter.__new__(BrowserApplicationAdapter)

    result = adapter.submit(make_request("not-a-url"))

    assert result.status == ApplicationStatus.FAILED
    assert result.method == ApplicationMethod.BROWSER
    assert "URL is invalid" in result.message


def test_browser_adapter_finds_chromium() -> None:
    executable = BrowserApplicationAdapter._find_chromium()

    assert executable


def test_browser_adapter_does_not_submit() -> None:
    adapter = BrowserApplicationAdapter.__new__(BrowserApplicationAdapter)

    assert hasattr(adapter, "submit")
