from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

from packages.application.browser.field_classifier import (
    BrowserFieldClassification,
    BrowserFieldKind,
)
from packages.application.browser.field_filler import BrowserFieldFiller
from packages.application.browser.field_inspector import BrowserField
from packages.application.browser.field_mapping import BrowserFieldMapping

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def make_field(
    *,
    element: str = "input",
    field_type: str = "text",
    name: str | None = None,
    field_id: str | None = None,
    label: str | None = None,
) -> BrowserField:
    return BrowserField(
        element=element,
        field_type=field_type,
        name=name,
        field_id=field_id,
        label=label,
        autocomplete=None,
        required=False,
        placeholder=None,
        value=None,
    )


def make_classification(
    kind: BrowserFieldKind,
    *,
    element: str = "input",
    field_type: str = "text",
    name: str | None = None,
    field_id: str | None = None,
    label: str | None = None,
) -> BrowserFieldClassification:
    return BrowserFieldClassification(
        field=make_field(
            element=element,
            field_type=field_type,
            name=name,
            field_id=field_id,
            label=label,
        ),
        kind=kind,
        confidence=1.0,
        reason="test classification",
    )


def make_mapping(
    kind: BrowserFieldKind,
    value: str | None,
    *,
    element: str = "input",
    field_type: str = "text",
    name: str | None = None,
    field_id: str | None = None,
    label: str | None = None,
    mappable: bool = True,
) -> BrowserFieldMapping:
    classification = make_classification(
        kind,
        element=element,
        field_type=field_type,
        name=name,
        field_id=field_id,
        label=label,
    )

    return BrowserFieldMapping(
        field=classification,
        value=value,
        source="test",
        mappable=mappable,
        reason="test mapping",
    )


def start_fixture_server() -> tuple[ThreadingHTTPServer, Thread]:
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        lambda *args, **kwargs: QuietHandler(
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


def test_fills_text_field_and_verifies() -> None:
    server, thread = start_fixture_server()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/application_form.html"
                )

                mapping = make_mapping(
                    BrowserFieldKind.FULL_NAME,
                    "Harshraj Engineer",
                    name="name",
                    field_id="name",
                )

                result = BrowserFieldFiller().fill(page, mapping)

                assert result.success is True
                assert page.locator("#name").input_value() == (
                    "Harshraj Engineer"
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_fills_email_field() -> None:
    server, thread = start_fixture_server()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/application_form.html"
                )

                mapping = make_mapping(
                    BrowserFieldKind.EMAIL,
                    "harshraj@example.com",
                    name="email",
                    field_id="email",
                    field_type="email",
                )

                result = BrowserFieldFiller().fill(page, mapping)

                assert result.success is True
                assert page.locator("#email").input_value() == (
                    "harshraj@example.com"
                )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_fills_phone_field() -> None:
    server, thread = start_fixture_server()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/application_form.html"
                )

                mapping = make_mapping(
                    BrowserFieldKind.PHONE,
                    "9876543210",
                    name="phone",
                    field_id="phone",
                    field_type="tel",
                )

                result = BrowserFieldFiller().fill(page, mapping)

                assert result.success is True
                assert page.locator("#phone").input_value() == "9876543210"
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_fills_resume_file(tmp_path: Path) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"%PDF-test")

    server, thread = start_fixture_server()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/application_form.html"
                )

                mapping = make_mapping(
                    BrowserFieldKind.RESUME,
                    str(resume),
                    name="resume",
                    field_id="resume",
                    field_type="file",
                )

                result = BrowserFieldFiller().fill(page, mapping)

                assert result.success is True
                assert page.locator("#resume").evaluate(
                    "element => element.files[0].name"
                ) == "resume.pdf"
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_fills_experience_select() -> None:
    server, thread = start_fixture_server()

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
                    "fresher",
                    element="select",
                    name="experience",
                    field_id="experience",
                )

                result = BrowserFieldFiller().fill(page, mapping)

                assert result.success is True
                assert page.locator("#experience").input_value() == "fresher"
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_does_not_fill_cover_letter() -> None:
    server, thread = start_fixture_server()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            try:
                page = browser.new_page()
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/application_form.html"
                )

                mapping = make_mapping(
                    BrowserFieldKind.COVER_LETTER,
                    None,
                    element="textarea",
                    name="cover_letter",
                    field_id="cover-letter",
                    mappable=False,
                )

                result = BrowserFieldFiller().fill(page, mapping)

                assert result.success is False
                assert page.locator("#cover-letter").input_value() == ""
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_does_not_fill_submit_button() -> None:
    server, thread = start_fixture_server()

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
                    element="button",
                    field_type="submit",
                    mappable=False,
                )

                result = BrowserFieldFiller().fill(page, mapping)

                assert result.success is False
                assert page.url.endswith("application_form.html")
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_missing_resume_is_rejected() -> None:
    mapping = make_mapping(
        BrowserFieldKind.RESUME,
        "/does/not/exist/resume.pdf",
        name="resume",
        field_id="resume",
        field_type="file",
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            page = browser.new_page()
            page.set_content(
                """
                <form>
                    <input id="resume" name="resume" type="file">
                </form>
                """
            )

            result = BrowserFieldFiller().fill(page, mapping)

            assert result.success is False
            assert "does not exist" in result.message
        finally:
            browser.close()


def test_ambiguous_target_is_rejected() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            page = browser.new_page()
            page.set_content(
                """
                <input name="email" type="email">
                <input name="email" type="email">
                """
            )

            mapping = make_mapping(
                BrowserFieldKind.EMAIL,
                "harshraj@example.com",
                name="email",
                field_id=None,
                field_type="email",
            )

            result = BrowserFieldFiller().fill(page, mapping)

            assert result.success is False
            assert "exactly one" in result.message
        finally:
            browser.close()
