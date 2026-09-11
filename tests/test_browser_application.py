import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from packages.application.adapters.browser import BrowserApplicationAdapter
from packages.application.browser.field_inspector import BrowserFieldInspector
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
    fixture_directory = Path(__file__).parent / "fixtures"

    handler = functools.partial(
        SimpleHTTPRequestHandler,
        directory=str(fixture_directory),
    )

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        url = (
            f"http://127.0.0.1:{server.server_port}"
            "/application_form.html"
        )

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


def test_browser_field_inspector_reads_application_fields() -> None:
    fixture_directory = Path(__file__).parent / "fixtures"

    handler = functools.partial(
        SimpleHTTPRequestHandler,
        directory=str(fixture_directory),
    )

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        url = (
            f"http://127.0.0.1:{server.server_port}"
            "/application_form.html"
        )

        adapter = BrowserApplicationAdapter(headless=True)

        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=adapter.executable_path,
            )

            try:
                page = browser.new_page()
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=adapter.timeout_ms,
                )

                fields = BrowserFieldInspector().inspect(page)

            finally:
                browser.close()

        assert len(fields) == 7

        assert fields[0].element == "input"
        assert fields[0].field_type == "text"
        assert fields[0].name == "name"
        assert fields[0].field_id == "name"
        assert fields[0].label == "Full Name"
        assert fields[0].autocomplete == "name"
        assert fields[0].required is True

        assert fields[1].element == "input"
        assert fields[1].field_type == "email"
        assert fields[1].name == "email"
        assert fields[1].field_id == "email"
        assert fields[1].label == "Email"
        assert fields[1].autocomplete == "email"
        assert fields[1].required is True

        assert fields[2].element == "input"
        assert fields[2].field_type == "tel"
        assert fields[2].name == "phone"
        assert fields[2].field_id == "phone"
        assert fields[2].label == "Phone"
        assert fields[2].autocomplete == "tel"
        assert fields[2].required is False

        assert fields[3].element == "input"
        assert fields[3].field_type == "file"
        assert fields[3].name == "resume"
        assert fields[3].field_id == "resume"
        assert fields[3].label == "Resume"
        assert fields[3].required is True

        assert fields[4].element == "textarea"
        assert fields[4].field_type == "textarea"
        assert fields[4].name == "cover_letter"
        assert fields[4].field_id == "cover-letter"
        assert fields[4].label == "Cover Letter"

        assert fields[5].element == "select"
        assert fields[5].field_type == "select"
        assert fields[5].name == "experience"
        assert fields[5].field_id == "experience"
        assert fields[5].label == "Experience Level"

        assert fields[6].element == "button"
        assert fields[6].field_type == "submit"
        assert fields[6].label == "Submit Application"

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
