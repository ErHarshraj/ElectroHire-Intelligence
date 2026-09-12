from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import Page, sync_playwright

from packages.application.browser.field_classifier import (
    BrowserFieldClassification,
    BrowserFieldKind,
)
from packages.application.browser.field_inspector import BrowserField
from packages.application.browser.field_mapping import BrowserFieldMapping
from packages.application.browser.form_validator import (
    BrowserApplicationPreview,
    BrowserFormValidator,
)
from packages.application.browser.submission_executor import (
    BrowserSubmissionExecutor,
    BrowserSubmissionStatus,
)

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
    value: str,
    field_type: str = "text",
    required: bool = False,
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
        source="candidate",
        mappable=True,
        reason="test",
    )


def make_valid_preview(
    page: Page,
    resume_path: Path,
) -> tuple[BrowserApplicationPreview, list[BrowserFieldMapping]]:
    page.locator("#name").fill("Harshraj")
    page.locator("#email").fill("harshraj@example.com")
    page.locator("#phone").fill("9876543210")
    page.locator("#resume").set_input_files(str(resume_path))

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
        make_mapping(
            BrowserFieldKind.RESUME,
            name="resume",
            field_id="resume",
            value=str(resume_path),
            field_type="file",
            required=True,
        ),
    ]

    preview = BrowserFormValidator().validate(
        page,
        mappings,
    )

    return preview, mappings


def test_successful_submission_is_confirmed(
    tmp_path: Path,
) -> None:
    server, _ = start_fixture_server()

    try:
        resume_path = tmp_path / "resume.pdf"
        resume_path.write_bytes(b"%PDF-1.4\nElectroHire test resume\n")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/"
                    "application_form.html"
                )

                preview, mappings = make_valid_preview(
                    page,
                    resume_path,
                )

                assert preview.valid is True

                result = BrowserSubmissionExecutor().submit(
                    page,
                    preview,
                    mappings,
                )

                assert result.status == BrowserSubmissionStatus.SUBMITTED
                assert "/application_success.html" in result.url
                assert result.confirmation_text is not None
                assert "submitted successfully" in (
                    result.confirmation_text.lower()
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


def test_invalid_preview_blocks_submission() -> None:
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

                mappings: list[BrowserFieldMapping] = []

                preview = BrowserFormValidator().validate(
                    page,
                    mappings,
                )

                assert preview.valid is False

                result = BrowserSubmissionExecutor().submit(
                    page,
                    preview,
                    mappings,
                )

                assert result.status == BrowserSubmissionStatus.FAILED
                assert result.message == "application form is not valid"
                assert page.url.endswith(
                    "/application_form.html"
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


def test_submit_mapping_is_rejected() -> None:
    server, _ = start_fixture_server()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/"
                    "application_success.html"
                )

                field = BrowserField(
                    element="button",
                    field_type="submit",
                    name=None,
                    field_id=None,
                    label="Submit",
                    autocomplete=None,
                    required=False,
                    placeholder=None,
                    value=None,
                )

                classification = BrowserFieldClassification(
                    field=field,
                    kind=BrowserFieldKind.SUBMIT,
                    confidence=1.0,
                    reason="test",
                )

                mapping = BrowserFieldMapping(
                    field=classification,
                    value=None,
                    source=None,
                    mappable=False,
                    reason="submit control",
                )

                preview = BrowserApplicationPreview(
                    url=page.url,
                    title=page.title(),
                    valid=True,
                    fields=[],
                    issues=[],
                )

                result = BrowserSubmissionExecutor().submit(
                    page,
                    preview,
                    [mapping],
                )

                assert result.status == BrowserSubmissionStatus.FAILED
                assert "submit control" in result.message
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
