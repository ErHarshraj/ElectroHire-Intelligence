"""
Browser application field classification.

Converts inspected HTML fields into application-level meanings.

This module is deterministic and does not interact with the browser.
It does not fill fields and does not submit forms.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from packages.application.browser.field_inspector import BrowserField


class BrowserFieldKind(str, Enum):
    """Semantic meaning of an application form field."""

    FULL_NAME = "full_name"
    EMAIL = "email"
    PHONE = "phone"
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    EXPERIENCE_LEVEL = "experience_level"
    SUBMIT = "submit"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class BrowserFieldClassification:
    """Classification result for one inspected browser field."""

    field: BrowserField
    kind: BrowserFieldKind
    confidence: float
    reason: str


class BrowserFieldClassifier:
    """
    Classify browser fields using deterministic metadata signals.

    Signals considered:
    - element type
    - HTML input type
    - name
    - id
    - label
    - autocomplete
    - placeholder
    """

    _NAME_KEYS = (
        "full name",
        "fullname",
        "full_name",
        "candidate name",
        "candidate_name",
        "applicant name",
        "applicant_name",
        "name",
    )

    _EMAIL_KEYS = (
        "email",
        "e-mail",
        "mail",
    )

    _PHONE_KEYS = (
        "phone",
        "telephone",
        "tel",
        "mobile",
        "mobile number",
        "mobile_number",
        "contact number",
        "contact_number",
    )

    _RESUME_KEYS = (
        "resume",
        "cv",
        "curriculum vitae",
    )

    _COVER_LETTER_KEYS = (
        "cover letter",
        "cover_letter",
        "coverletter",
        "motivation letter",
        "motivation_letter",
    )

    _EXPERIENCE_KEYS = (
        "experience",
        "experience level",
        "experience_level",
        "years of experience",
        "years_of_experience",
        "seniority",
    )

    def classify(
        self,
        field: BrowserField,
    ) -> BrowserFieldClassification:
        """Classify one browser field."""

        if field.element == "button":
            if field.field_type.lower() == "submit":
                return BrowserFieldClassification(
                    field=field,
                    kind=BrowserFieldKind.SUBMIT,
                    confidence=1.0,
                    reason="button has type=submit",
                )

            if self._contains_any(
                field.label,
                ("submit", "apply", "send application"),
            ):
                return BrowserFieldClassification(
                    field=field,
                    kind=BrowserFieldKind.SUBMIT,
                    confidence=0.85,
                    reason="button label indicates application submission",
                )

            return BrowserFieldClassification(
                field=field,
                kind=BrowserFieldKind.UNKNOWN,
                confidence=0.0,
                reason="button does not identify an application submission action",
            )

        if field.element == "input":
            input_type = field.field_type.lower()

            if input_type == "file":
                if self._contains_any(
                    self._combined_text(field),
                    self._RESUME_KEYS,
                ):
                    return BrowserFieldClassification(
                        field=field,
                        kind=BrowserFieldKind.RESUME,
                        confidence=1.0,
                        reason="file input metadata identifies resume/CV",
                    )

                return BrowserFieldClassification(
                    field=field,
                    kind=BrowserFieldKind.UNKNOWN,
                    confidence=0.0,
                    reason="file input has no deterministic resume/CV signal",
                )

            if input_type == "email":
                return BrowserFieldClassification(
                    field=field,
                    kind=BrowserFieldKind.EMAIL,
                    confidence=1.0,
                    reason="input type=email",
                )

            if input_type == "tel":
                return BrowserFieldClassification(
                    field=field,
                    kind=BrowserFieldKind.PHONE,
                    confidence=1.0,
                    reason="input type=tel",
                )

        text = self._combined_text(field)

        if self._contains_any(text, self._EMAIL_KEYS):
            return BrowserFieldClassification(
                field=field,
                kind=BrowserFieldKind.EMAIL,
                confidence=0.95,
                reason="field metadata identifies email",
            )

        if self._contains_any(text, self._PHONE_KEYS):
            return BrowserFieldClassification(
                field=field,
                kind=BrowserFieldKind.PHONE,
                confidence=0.95,
                reason="field metadata identifies phone",
            )

        if self._contains_any(text, self._RESUME_KEYS):
            return BrowserFieldClassification(
                field=field,
                kind=BrowserFieldKind.RESUME,
                confidence=0.95,
                reason="field metadata identifies resume/CV",
            )

        if self._contains_any(text, self._COVER_LETTER_KEYS):
            return BrowserFieldClassification(
                field=field,
                kind=BrowserFieldKind.COVER_LETTER,
                confidence=0.95,
                reason="field metadata identifies cover letter",
            )

        if self._contains_any(text, self._EXPERIENCE_KEYS):
            return BrowserFieldClassification(
                field=field,
                kind=BrowserFieldKind.EXPERIENCE_LEVEL,
                confidence=0.90,
                reason="field metadata identifies experience",
            )

        if self._contains_any(text, self._NAME_KEYS):
            return BrowserFieldClassification(
                field=field,
                kind=BrowserFieldKind.FULL_NAME,
                confidence=0.90,
                reason="field metadata identifies candidate name",
            )

        return BrowserFieldClassification(
            field=field,
            kind=BrowserFieldKind.UNKNOWN,
            confidence=0.0,
            reason="no deterministic semantic signal matched",
        )

    def classify_all(
        self,
        fields: list[BrowserField],
    ) -> list[BrowserFieldClassification]:
        """Classify every inspected browser field."""

        return [self.classify(field) for field in fields]

    @staticmethod
    def _combined_text(field: BrowserField) -> str:
        """Combine searchable field metadata into normalized text."""

        values = (
            field.name,
            field.field_id,
            field.label,
            field.autocomplete,
            field.placeholder,
            field.field_type,
        )

        return " ".join(
            value.strip().lower()
            for value in values
            if value
        )

    @staticmethod
    def _contains_any(
        text: str | None,
        keys: tuple[str, ...],
    ) -> bool:
        """Return True when normalized text contains one of the supplied keys."""

        if not text:
            return False

        normalized = text.strip().lower()

        return any(
            key in normalized
            for key in keys
        )
