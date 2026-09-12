from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

from packages.application.browser.field_classifier import (
    BrowserFieldClassification,
    BrowserFieldKind,
)
from packages.application.browser.field_inspector import BrowserField
from packages.application.browser.field_mapping import BrowserFieldMapping
from packages.application.browser.form_validator import BrowserFormValidator

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def make_field(
    kind: BrowserFieldKind,
    *,
    name: str | None = None,
    field_id: str | None = None,
    field_type: str = "text",
    required: bool = False,
) -> BrowserField:
    return BrowserField(
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


def make_classification(
    kind: BrowserFieldKind,
    *,
    name: str | None = None,
    field_id: str | None = None,
    field_type: str = "text",
    required: bool = False,
) -> BrowserFieldClassification:
    field = make_field(
        kind,
        name=name,
        field_id=field_id,
        field_type=field_type,
        required=required,
    )

    return BrowserFieldClassification(
        field=field,
        kind=kind,
        confidence=1.0,
        reason="test",
    )


def make_mapping(
    kind: BrowserFieldKind,
    value: str | None,
    *,
    name: str | None = None,
    field_id: str | None = None,
    field_type: str = "text",
    required: bool = False,
    mappable: bool = True,
    source: str | None = "test",
    reason: str = "test",
) -> BrowserFieldMapping:
    classification = make_classification(
        kind,
        name=name,
        field_id=field_id,
        field_type=field_type,
        required=required,
    )

    return BrowserFieldMapping(
        field=classification,
        value=value,
        source=source,
        mappable=mappable,
        reason=reason,
    )


def start_fixture_server() -> tuple[ThreadingHTTPServer, Thread]:
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: SimpleHTTPRequestHandler(
            *args,
            directory=str(FIXTURE_DIR),
            **kwargs,
        ),
    )

    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    return server, thread


def test_required_resume_is_detected_without_attachment() -> None:
    server, _ = start_fixture_server()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/application_form.html"
                )

                page.locator("#name").fill("Harshraj")
                page.locator("#email").fill("harshraj@example.com")
                page.locator("#phone").fill("9876543210")
                page.locator("#experience").select_option("fresher")

                mappings = [
                    make_mapping(
                        BrowserFieldKind.FULL_NAME,
                        "Harshraj",
                        name="name",
                        field_id="name",
                        required=True,
                    ),
                    make_mapping(
                        BrowserFieldKind.EMAIL,
                        "harshraj@example.com",
                        name="email",
                        field_id="email",
                        field_type="email",
                        required=True,
                    ),
                    make_mapping(
                        BrowserFieldKind.PHONE,
                        "9876543210",
                        name="phone",
                        field_id="phone",
                        field_type="tel",
                    ),
                    make_mapping(
                        BrowserFieldKind.EXPERIENCE_LEVEL,
                        "fresher",
                        name="experience",
                        field_id="experience",
                    ),
                ]

                result = BrowserFormValidator().validate(
                    page,
                    mappings,
                )

                assert result.valid is False
                assert any(
                    "resume" in issue.lower()
                    for issue in result.issues
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


def test_required_unmapped_field_is_detected() -> None:
    server, _ = start_fixture_server()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/application_form.html"
                )

                mappings = [
                    make_mapping(
                        BrowserFieldKind.FULL_NAME,
                        "Harshraj",
                        name="name",
                        field_id="name",
                        required=True,
                    ),
                ]

                result = BrowserFormValidator().validate(
                    page,
                    mappings,
                )

                assert result.valid is False
                assert any(
                    "required field is not mapped" in issue
                    for issue in result.issues
                )
                assert any(
                    "email" in issue.lower()
                    for issue in result.issues
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


def test_wrong_filled_value_is_rejected() -> None:
    server, _ = start_fixture_server()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/application_form.html"
                )

                page.locator("#name").fill("Wrong Name")

                mapping = make_mapping(
                    BrowserFieldKind.FULL_NAME,
                    "Harshraj",
                    name="name",
                    field_id="name",
                )

                result = BrowserFormValidator().validate(
                    page,
                    [mapping],
                )

                assert result.valid is False
                assert any(
                    "expected 'Harshraj'" in issue
                    for issue in result.issues
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


def test_cover_letter_requires_generated_content() -> None:
    server, _ = start_fixture_server()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/application_form.html"
                )

                field = BrowserField(
                    element="textarea",
                    field_type="textarea",
                    name="cover_letter",
                    field_id="cover-letter",
                    label="Cover Letter",
                    autocomplete=None,
                    required=False,
                    placeholder=None,
                    value="",
                )

                classification = BrowserFieldClassification(
                    field=field,
                    kind=BrowserFieldKind.COVER_LETTER,
                    confidence=1.0,
                    reason="test",
                )

                mapping = BrowserFieldMapping(
                    field=classification,
                    value=None,
                    source="generated_cover_letter",
                    mappable=False,
                    reason="cover letter requires generated application content",
                )

                result = BrowserFormValidator().validate(
                    page,
                    [mapping],
                )

                assert result.valid is False
                assert any(
                    "cover letter requires generated application content"
                    in issue
                    for issue in result.issues
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


def test_submit_control_is_rejected() -> None:
    server, _ = start_fixture_server()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/application_form.html"
                )

                mapping = make_mapping(
                    BrowserFieldKind.SUBMIT,
                    None,
                    name=None,
                    field_id="submit",
                    field_type="submit",
                )

                result = BrowserFormValidator().validate(
                    page,
                    [mapping],
                )

                assert result.valid is False
                assert any(
                    "submit control" in issue
                    for issue in result.issues
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()


def test_invalid_select_value_is_rejected() -> None:
    server, _ = start_fixture_server()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/application_form.html"
                )

                mapping = make_mapping(
                    BrowserFieldKind.EXPERIENCE_LEVEL,
                    "senior",
                    name="experience",
                    field_id="experience",
                )

                result = BrowserFormValidator().validate(
                    page,
                    [mapping],
                )

                assert result.valid is False
                assert any(
                    "select option 'senior' is not available" in issue
                    for issue in result.issues
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
