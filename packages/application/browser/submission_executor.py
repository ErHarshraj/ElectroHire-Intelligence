"""
Automatic browser application submission.

This module submits an already-prepared and validated application form.
It does not bypass authentication, CAPTCHA, or anti-bot protections.

Submission results are classified as:
- SUBMITTED: successful submission was detected.
- FAILED: submission could not be performed.
- UNCERTAIN: the submit action occurred, but success could not be
  established safely.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from packages.application.browser.field_classifier import BrowserFieldKind
from packages.application.browser.field_mapping import BrowserFieldMapping
from packages.application.browser.form_validator import BrowserApplicationPreview


class BrowserSubmissionStatus(str, Enum):
    """Result of an automatic browser submission attempt."""

    SUBMITTED = "submitted"
    FAILED = "failed"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class BrowserSubmissionResult:
    """Result returned after attempting browser submission."""

    status: BrowserSubmissionStatus
    url: str
    message: str
    confirmation_text: str | None = None


class BrowserSubmissionExecutor:
    """Submit a validated browser application automatically."""

    SUCCESS_SELECTORS = (
        "[data-application-success]",
        "[data-submission-success]",
        ".application-success",
        ".submission-success",
        "#application-success",
        "#submission-success",
    )

    SUCCESS_PHRASES = (
        "application submitted",
        "application has been submitted",
        "successfully submitted",
        "thank you for applying",
        "thank you for your application",
        "application received",
        "application was received",
    )

    def __init__(self, timeout_ms: int = 15000) -> None:
        self._timeout_ms = timeout_ms

    def submit(
        self,
        page: Page,
        preview: BrowserApplicationPreview,
        mappings: list[BrowserFieldMapping],
    ) -> BrowserSubmissionResult:
        """Submit a validated application form."""

        if not preview.valid:
            return BrowserSubmissionResult(
                status=BrowserSubmissionStatus.FAILED,
                url=page.url,
                message="application form is not valid",
            )

        if self._contains_submit_mapping(mappings):
            return BrowserSubmissionResult(
                status=BrowserSubmissionStatus.FAILED,
                url=page.url,
                message="submit control must not be supplied as application data",
            )

        submit_locator = self._resolve_submit_control(page)

        if submit_locator is None:
            return BrowserSubmissionResult(
                status=BrowserSubmissionStatus.FAILED,
                url=page.url,
                message="no unique submit control was found",
            )

        try:
            submit_locator.click(timeout=self._timeout_ms)
        except Exception as exc:
            return BrowserSubmissionResult(
                status=BrowserSubmissionStatus.FAILED,
                url=page.url,
                message=(
                    "submit control could not be activated: "
                    f"{type(exc).__name__}: {exc}"
                ),
            )

        confirmation = self._find_confirmation(page)

        if confirmation is not None:
            return BrowserSubmissionResult(
                status=BrowserSubmissionStatus.SUBMITTED,
                url=page.url,
                message="application submission confirmed",
                confirmation_text=confirmation,
            )

        return BrowserSubmissionResult(
            status=BrowserSubmissionStatus.UNCERTAIN,
            url=page.url,
            message=(
                "submit control was activated, but application "
                "submission could not be confirmed"
            ),
        )

    @staticmethod
    def _contains_submit_mapping(
        mappings: list[BrowserFieldMapping],
    ) -> bool:
        return any(
            mapping.field.kind == BrowserFieldKind.SUBMIT
            for mapping in mappings
        )

    @staticmethod
    def _resolve_submit_control(page: Page) -> Locator | None:
        """Find exactly one usable submit control."""

        selectors = (
            'button[type="submit"]',
            'input[type="submit"]',
            'button:not([type])',
        )

        matches: list[Locator] = []

        for selector in selectors:
            locator = page.locator(selector)
            count = locator.count()

            for index in range(count):
                matches.append(locator.nth(index))

        if len(matches) != 1:
            return None

        return matches[0]

    def _find_confirmation(self, page: Page) -> str | None:
        """Look for an explicit submission confirmation."""

        for selector in self.SUCCESS_SELECTORS:
            locator = page.locator(selector)

            if locator.count() != 1:
                continue

            try:
                if not locator.is_visible(timeout=self._timeout_ms):
                    continue

                text = locator.inner_text().strip()

                if text:
                    return text
            except PlaywrightTimeoutError:
                continue

        body_text = page.locator("body").inner_text().strip()

        normalized = " ".join(body_text.lower().split())

        for phrase in self.SUCCESS_PHRASES:
            if phrase in normalized:
                return body_text

        return None
