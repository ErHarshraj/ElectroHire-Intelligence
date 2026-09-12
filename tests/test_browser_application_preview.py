from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

from packages.application.browser.application_preview import (
    BrowserApplicationPreviewBuilder,
)
from packages.application.browser.field_classifier import (
    BrowserFieldClassification,
    BrowserFieldKind,
)
from packages.application.browser.field_inspector import BrowserField
from packages.application.browser.field_mapping import BrowserFieldMapping

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def start_fixture_server() -> tuple[ThreadingHTTPServer, Thread]:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: SimpleHTTPRequestHandler(
            *args,
            directory=str(FIXTURE_DIR),
            **kwargs,
        ),
    )

    thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    return server, thread


def make_mapping(
    kind: BrowserFieldKind,
    *,
    name: str,
    field_id: str,
    value: str | None,
    field_type: str = "text",
    required: bool = False,
    mappable: bool = True,
    source: str = "candidate",
    reason: str = "test",
) -> BrowserFieldMapping:
    field = BrowserField(
        element="input",
        field_type=field_type,
        name=name,
        field_id=field_id,
        label=None,
        autocomplete=None,
        required=required,
        placeholder=None,
        value=None,
    )

    classification = BrowserFieldClassification(
        field=field,
        kind=kind,
        confidence=1.0,
        reason="test",
    )

    return BrowserFieldMapping(
        field=classification,
        value=value,
        source=source,
        mappable=mappable,
        reason=reason,
    )


def test_application_preview_reports_missing_resume() -> None:
    server, _ = start_fixture_server()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/"
                    "application_form.html"
                )

                page.locator("#name").fill("Harshraj")
                page.locator("#email").fill("harshraj@example.com")
                page.locator("#phone").fill("9876543210")

                mappings = [
                    make_mapping(
                        BrowserFieldKind.FULL_NAME,
                        name="name",
                        field_id="name",
                        value="Harshraj",
                        required=True,
                    ),
                    make_mapping(
                        BrowserFieldKind.EMAIL,
                        name="email",
                        field_id="email",
                        value="harshraj@example.com",
                        field_type="email",
                        required=True,
                    ),
                    make_mapping(
                        BrowserFieldKind.PHONE,
                        name="phone",
                        field_id="phone",
                        value="9876543210",
                    ),
                ]

                result = BrowserApplicationPreviewBuilder().build(
                    page,
                    mappings,
                )

                assert result.valid is False
                assert result.url.endswith(
                    "/application_form.html"
                )
                assert result.title == "ElectroHire Test Application"
                assert result.mapped_fields == 3
                assert result.valid_fields == 3
                assert result.invalid_fields == 0
                assert any(
                    "resume" in issue.lower()
                    for issue in result.issues
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


def test_invalid_mapping_appears_in_preview() -> None:
    server, _ = start_fixture_server()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/"
                    "application_form.html"
                )

                page.locator("#name").fill("Wrong Name")

                mapping = make_mapping(
                    BrowserFieldKind.FULL_NAME,
                    name="name",
                    field_id="name",
                    value="Harshraj",
                )

                result = BrowserApplicationPreviewBuilder().build(
                    page,
                    [mapping],
                )

                assert result.valid is False
                assert result.mapped_fields == 1
                assert result.valid_fields == 0
                assert result.invalid_fields == 1
                assert any(
                    "expected 'Harshraj'" in issue
                    for issue in result.issues
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
