"""
Automatic browser application adapter.

The adapter orchestrates the complete browser application flow:

1. Open the application URL.
2. Inspect the form.
3. Classify fields.
4. Map candidate data.
5. Fill only approved fields.
6. Validate the prepared form.
7. Run browser safety checks.
8. Submit automatically.
9. Confirm submission.

It does not bypass authentication, CAPTCHA, anti-bot protections,
or other access controls.
"""

from __future__ import annotations

import shutil
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from packages.application.adapters.base import ApplicationAdapter
from packages.application.browser.application_preview import (
    BrowserApplicationPreviewBuilder,
)
from packages.application.browser.field_classifier import (
    BrowserFieldClassifier,
    BrowserFieldKind,
)
from packages.application.browser.field_filler import BrowserFieldFiller
from packages.application.browser.field_inspector import BrowserFieldInspector
from packages.application.browser.field_mapping import BrowserFieldMapper
from packages.application.browser.form_validator import BrowserFormValidator
from packages.application.browser.safety import (
    BrowserApplicationSafetyGuard,
)
from packages.application.browser.submission_executor import (
    BrowserSubmissionExecutor,
    BrowserSubmissionStatus,
)
from packages.application.models import (
    ApplicationRequest,
    ApplicationResult,
    ApplicationStatus,
)
from packages.application.profile import CandidateProfile


class BrowserApplicationAdapter(ApplicationAdapter):
    """Automatically prepare and submit browser applications."""

    FILLABLE_KINDS = {
        BrowserFieldKind.FULL_NAME,
        BrowserFieldKind.EMAIL,
        BrowserFieldKind.PHONE,
        BrowserFieldKind.RESUME,
        BrowserFieldKind.EXPERIENCE_LEVEL,
    }

    def __init__(
        self,
        candidate: CandidateProfile | None = None,
        headless: bool = True,
        timeout_ms: int = 15000,
        executable_path: str | None = None,
    ) -> None:
        self.candidate = candidate
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.executable_path = executable_path or self._find_chromium()
        self.inspector = BrowserFieldInspector()
        self.classifier = BrowserFieldClassifier()
        self.mapper = BrowserFieldMapper()
        self.filler = BrowserFieldFiller()
        self.validator = BrowserFormValidator()
        self.preview_builder = BrowserApplicationPreviewBuilder(
            validator=self.validator,
        )
        self.safety_guard = BrowserApplicationSafetyGuard()
        self.submission_executor = BrowserSubmissionExecutor(
            timeout_ms=timeout_ms,
        )

    def submit(self, request: ApplicationRequest) -> ApplicationResult:
        """Execute the complete browser application flow."""

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

        if self.candidate is None:
            return ApplicationResult(
                status=ApplicationStatus.FAILED,
                method=request.application_method,
                message="candidate profile is required for browser applications",
            )

        try:
            return self._execute(request)
        except Exception as exc:
            return ApplicationResult(
                status=ApplicationStatus.PAUSED,
                method=request.application_method,
                message=(
                    "browser application interrupted: "
                    f"{type(exc).__name__}: {exc}"
                ),
            )

    def _execute(self, request: ApplicationRequest) -> ApplicationResult:
        """Run one complete browser application attempt."""

        assert request.apply_url is not None
        assert self.candidate is not None

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=self.headless,
                executable_path=self.executable_path,
            )

            try:
                page = browser.new_page()
                page.set_default_timeout(self.timeout_ms)

                response = page.goto(
                    request.apply_url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms,
                )

                if response is None:
                    return ApplicationResult(
                        status=ApplicationStatus.FAILED,
                        method=request.application_method,
                        message="browser application page returned no response",
                    )

                if response.status >= 400:
                    return ApplicationResult(
                        status=ApplicationStatus.FAILED,
                        method=request.application_method,
                        message=(
                            "browser application page returned HTTP "
                            f"{response.status}"
                        ),
                    )

                inspected_fields = self.inspector.inspect(page)

                classifications = [
                    self.classifier.classify(field)
                    for field in inspected_fields
                ]

                mappings = self.mapper.map_all(
                    classifications,
                    self.candidate,
                )

                fillable_mappings = [
                    mapping
                    for mapping in mappings
                    if mapping.field.kind in self.FILLABLE_KINDS
                ]

                fill_results = self.filler.fill_all(
                    page,
                    fillable_mappings,
                )

                fill_failures = [
                    result.message
                    for result in fill_results
                    if not result.success
                ]

                if fill_failures:
                    return ApplicationResult(
                        status=ApplicationStatus.FAILED,
                        method=request.application_method,
                        message=(
                            "browser application field filling failed: "
                            + "; ".join(fill_failures)
                        ),
                    )

                preview = self.preview_builder.build(
                    page,
                    fillable_mappings,
                )

                if not preview.valid:
                    return ApplicationResult(
                        status=ApplicationStatus.FAILED,
                        method=request.application_method,
                        message=(
                            "browser application validation failed: "
                            + "; ".join(preview.issues)
                        ),
                    )

                full_preview = self.validator.validate(page, mappings)

                submit_controls = page.locator(
                    'button[type="submit"], '
                    'input[type="submit"], '
                    'button:not([type])'
                )

                submit_control_count = submit_controls.count()

                safety = self.safety_guard.evaluate(
                    application_url=request.apply_url,
                    current_url=page.url,
                    preview=full_preview,
                    fields=classifications,
                    submit_control_count=submit_control_count,
                    submission_authorized=request.submission_authorized,
                )

                if not safety.allowed:
                    return ApplicationResult(
                        status=ApplicationStatus.PAUSED,
                        method=request.application_method,
                        message=(
                            "browser application blocked by safety guard: "
                            + safety.reason
                        ),
                        external_reference=page.url,
                    )

                submission = self.submission_executor.submit(
                    page,
                    full_preview,
                    fillable_mappings,
                )

                if submission.status == BrowserSubmissionStatus.SUBMITTED:
                    confirmation = submission.confirmation_text or ""
                    message = submission.message

                    if confirmation:
                        message = f"{message}: {confirmation}"

                    return ApplicationResult(
                        status=ApplicationStatus.SUBMITTED,
                        method=request.application_method,
                        message=message,
                        external_reference=page.url,
                    )

                if submission.status == BrowserSubmissionStatus.UNCERTAIN:
                    return ApplicationResult(
                        status=ApplicationStatus.PAUSED,
                        method=request.application_method,
                        message=submission.message,
                        external_reference=page.url,
                    )

                return ApplicationResult(
                    status=ApplicationStatus.FAILED,
                    method=request.application_method,
                    message=submission.message,
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
