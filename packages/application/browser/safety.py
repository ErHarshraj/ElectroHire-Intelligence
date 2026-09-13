"""
Browser application safety guard.

Prevents browser submission when the application page or form
contains conditions that are unsafe for unattended automation.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from packages.application.browser.application_preview import (
    BrowserApplicationPreview,
)
from packages.application.browser.field_classifier import (
    BrowserFieldClassification,
    BrowserFieldKind,
)


@dataclass(frozen=True)
class BrowserSafetyResult:
    allowed: bool
    reason: str


class BrowserApplicationSafetyGuard:
    """Apply hard safety checks before browser submission."""

    BLOCKED_FIELD_TYPES = {
        "password",
    }

    BLOCKED_FIELD_TERMS = {
        "captcha",
        "recaptcha",
        "hcaptcha",
        "turnstile",
        "verification code",
        "otp",
        "one-time password",
    }

    def evaluate(
        self,
        application_url: str,
        current_url: str,
        preview: BrowserApplicationPreview,
        fields: list[BrowserFieldClassification],
        submit_control_count: int,
        approved: bool,
    ) -> BrowserSafetyResult:
        """Return whether browser submission is safe to proceed."""

        if not approved:
            return BrowserSafetyResult(
                allowed=False,
                reason="explicit application approval is required",
            )

        if not preview.valid:
            return BrowserSafetyResult(
                allowed=False,
                reason="application preview is invalid",
            )

        if not self._same_origin(application_url, current_url):
            return BrowserSafetyResult(
                allowed=False,
                reason="application page redirected to a different origin",
            )

        if submit_control_count != 1:
            return BrowserSafetyResult(
                allowed=False,
                reason=(
                    "application form must contain exactly one "
                    "submit control"
                ),
            )

        for field in fields:
            if self._is_blocked_field(field):
                return BrowserSafetyResult(
                    allowed=False,
                    reason=(
                        "blocked authentication or anti-bot field detected: "
                        f"{field.field.field_type}"
                    ),
                )

            if self._contains_blocked_term(field):
                return BrowserSafetyResult(
                    allowed=False,
                    reason=(
                        "blocked authentication or anti-bot field detected: "
                        f"{field.field.label or field.field.name or field.field.field_id}"
                    ),
                )

        for field in fields:
            if (
                field.field.required
                and field.kind == BrowserFieldKind.UNKNOWN
            ):
                return BrowserSafetyResult(
                    allowed=False,
                    reason="unknown required application field detected",
                )

        return BrowserSafetyResult(
            allowed=True,
            reason="browser application passed safety checks",
        )

    @staticmethod
    def _same_origin(application_url: str, current_url: str) -> bool:
        """Require the final page to remain on the original origin."""

        expected = urlparse(application_url)
        current = urlparse(current_url)

        return (
            expected.scheme in {"http", "https"}
            and current.scheme in {"http", "https"}
            and expected.hostname == current.hostname
            and expected.port == current.port
        )

    def _is_blocked_field(
        self,
        field: BrowserFieldClassification,
    ) -> bool:
        """Detect password/authentication controls."""

        field_type = field.field.field_type.lower().strip()

        if field_type in self.BLOCKED_FIELD_TYPES:
            return True

        return field.kind not in {
            BrowserFieldKind.FULL_NAME,
            BrowserFieldKind.EMAIL,
            BrowserFieldKind.PHONE,
            BrowserFieldKind.RESUME,
            BrowserFieldKind.COVER_LETTER,
            BrowserFieldKind.EXPERIENCE_LEVEL,
            BrowserFieldKind.SUBMIT,
            BrowserFieldKind.UNKNOWN,
        }

    def _contains_blocked_term(
        self,
        field: BrowserFieldClassification,
    ) -> bool:
        """Detect CAPTCHA, OTP, and authentication terminology."""

        values = (
            field.field.name,
            field.field.field_id,
            field.field.label,
            field.field.placeholder,
            field.field.autocomplete,
        )

        normalized_values = {
            value.lower().strip()
            for value in values
            if value
        }

        return any(
            term in value
            for value in normalized_values
            for term in self.BLOCKED_FIELD_TERMS
        )
