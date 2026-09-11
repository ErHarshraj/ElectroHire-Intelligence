"""
Browser application adapter.

Phase 1:
- Opens an application URL.
- Verifies that the page loads.
- Inspects basic application-form structure.
- Does NOT fill fields.
- Does NOT submit forms.
"""

from __future__ import annotations

import shutil
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from packages.application.adapters.base import ApplicationAdapter
from packages.application.models import ApplicationRequest, ApplicationResult, ApplicationStatus


class BrowserApplicationAdapter(ApplicationAdapter):
    """Safely inspect browser application targets without submitting."""

    def __init__(
        self,
        headless: bool = True,
        timeout_ms: int = 15000,
        executable_path: str | None = None,
    ) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.executable_path = executable_path or self._find_chromium()

    def submit(self, request: ApplicationRequest) -> ApplicationResult:
        """
        Inspect the application page.

        The method name is inherited from ApplicationAdapter, but this
        Phase 1 implementation deliberately performs no submission.
        """

        if not request.apply_url:
            return ApplicationResult(
                status=ApplicationStatus.FAILED,
                method=request.application_method,
                message="browser application URL is missing",
            )

        if not self._is_valid_url(request.apply_url):
            return ApplicationResult(
                status=ApplicationStatus.FAILED,
                method=request.application_method,
                message="browser application URL is invalid",
            )

        try:
            inspection = self._inspect_page(request.apply_url)

            return ApplicationResult(
                status=ApplicationStatus.PENDING,
                method=request.application_method,
                message=inspection,
            )

        except Exception as exc:
            return ApplicationResult(
                status=ApplicationStatus.PAUSED,
                method=request.application_method,
                message=f"browser inspection interrupted: {type(exc).__name__}: {exc}",
            )

    def _inspect_page(self, url: str) -> str:
        """Open and inspect a page without interacting with its form."""

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=self.headless,
                executable_path=self.executable_path,
            )

            try:
                page = browser.new_page()
                page.set_default_timeout(self.timeout_ms)

                response = page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms,
                )

                title = page.title().strip()

                form_count = page.locator("form").count()
                input_count = page.locator("input").count()
                textarea_count = page.locator("textarea").count()
                select_count = page.locator("select").count()
                button_count = page.locator("button").count()

                status_code = response.status if response else None

                return (
                    "browser inspection completed; "
                    f"url={page.url}; "
                    f"http_status={status_code}; "
                    f"title={title!r}; "
                    f"forms={form_count}; "
                    f"inputs={input_count}; "
                    f"textareas={textarea_count}; "
                    f"selects={select_count}; "
                    f"buttons={button_count}; "
                    "submission=disabled"
                )
            finally:
                browser.close()

    @staticmethod
    def _find_chromium() -> str:
        """Find an already-installed Chromium executable."""

        candidates = (
            "chromium",
            "chromium-browser",
            "google-chrome",
            "google-chrome-stable",
        )

        for candidate in candidates:
            executable = shutil.which(candidate)

            if executable:
                return executable

        raise RuntimeError(
            "Chromium executable was not found. "
            "Set BROWSER_EXECUTABLE_PATH in the environment."
        )

    @staticmethod
    def _is_valid_url(value: str) -> bool:
        parsed = urlparse(value)

        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
        )
