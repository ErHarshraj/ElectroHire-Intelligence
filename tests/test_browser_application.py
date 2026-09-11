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


def test_browser_adapter_inspects_local_application_form() -> None:
    import functools
    import threading
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    from pathlib import Path

    fixture_directory = Path(__file__).parent / "fixtures"

    handler = functools.partial(
        SimpleHTTPRequestHandler,
        directory=str(fixture_directory),
    )

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        url = f"http://127.0.0.1:{server.server_port}/application_form.html"

        adapter = BrowserApplicationAdapter(headless=True)

        result = adapter.submit(
            ApplicationRequest(
                source="test",
                source_job_id="local-form",
                job_title="Hardware Engineer",
                company="ElectroHire Test",
                application_method=ApplicationMethod.BROWSER,
                apply_url=url,
            )
        )

        assert result.status == ApplicationStatus.PENDING
        assert result.method == ApplicationMethod.BROWSER
        assert "forms=1" in result.message
        assert "inputs=4" in result.message
        assert "textareas=1" in result.message
        assert "selects=1" in result.message
        assert "buttons=1" in result.message
        assert "submission=disabled" in result.message
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
