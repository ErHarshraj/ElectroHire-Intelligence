"""
Browser application field classification.

Converts inspected HTML fields into application-level meanings.

This module is deterministic and does not interact with the browser.
It does not fill fields and does not submit forms.
"""

from __future__ import annotations

import re
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

    The classifier intentionally prefers UNKNOWN over an unsafe guess.
    """

    _NAME_PHRASES = (
        "full name",
        "full_name",
        "fullname",
        "candidate name",
        "candidate_name",
        "applicant name",
        "applicant_name",
    )

    _NAME_EXACT = {
        "name",
        "candidate",
        "applicant",
    }

    _EMAIL_PHRASES = (
        "email",
        "e-mail",
        "email address",
        "email_address",
    )

    _PHONE_PHRASES = (
        "phone",
        "telephone",
        "mobile",
        "mobile number",
        "mobile_number",
        "phone number",
        "phone_number",
        "telephone number",
        "telephone_number",
        "contact number",
        "contact_number",
    )

    _PHONE_EXACT = {
        "tel",
        "phone",
        "mobile",
        "telephone",
    }

    _RESUME_PHRASES = (
        "resume",
        "cv",
        "curriculum vitae",
        "resume upload",
        "resume_upload",
        "cv upload",
        "cv_upload",
    )

    _COVER_LETTER_PHRASES = (
        "cover letter",
        "cover_letter",
        "coverletter",
        "motivation letter",
        "motivation_letter",
    )

    _EXPERIENCE_PHRASES = (
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

            if self._contains_phrase(
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
            input_type = field.field_type.lower().strip()

            if input_type == "file":
                if self._contains_any_metadata(
                    field,
                    self._RESUME_PHRASES,
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

        if self._contains_any_metadata(field, self._EMAIL_PHRASES):
            return BrowserFieldClassification(
                field=field,
                kind=BrowserFieldKind.EMAIL,
                confidence=0.95,
                reason="field metadata identifies email",
            )

        if self._contains_any_metadata(field, self._PHONE_PHRASES):
            return BrowserFieldClassification(
                field=field,
                kind=BrowserFieldKind.PHONE,
                confidence=0.95,
                reason="field metadata identifies phone",
            )

        if self._contains_any_metadata(field, self._RESUME_PHRASES):
            return BrowserFieldClassification(
                field=field,
                kind=BrowserFieldKind.RESUME,
                confidence=0.95,
                reason="field metadata identifies resume/CV",
            )

        if self._contains_any_metadata(
            field,
            self._COVER_LETTER_PHRASES,
        ):
            return BrowserFieldClassification(
                field=field,
                kind=BrowserFieldKind.COVER_LETTER,
                confidence=0.95,
                reason="field metadata identifies cover letter",
            )

        if self._contains_any_metadata(
            field,
            self._EXPERIENCE_PHRASES,
        ):
            return BrowserFieldClassification(
                field=field,
                kind=BrowserFieldKind.EXPERIENCE_LEVEL,
                confidence=0.90,
                reason="field metadata identifies experience",
            )

        if self._has_name_signal(field):
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

    @classmethod
    def _has_name_signal(cls, field: BrowserField) -> bool:
        """Return whether metadata contains a safe name-field signal."""

        metadata = cls._metadata_values(field)

        for value in metadata:
            normalized = cls._normalize(value)

            if normalized in cls._NAME_EXACT:
                return True

            if cls._contains_phrase(
                normalized,
                cls._NAME_PHRASES,
            ):
                return True

        return False

    @classmethod
    def _contains_any_metadata(
        cls,
        field: BrowserField,
        phrases: tuple[str, ...],
    ) -> bool:
        """Return True when any field metadata matches a known phrase."""

        for value in cls._metadata_values(field):
            normalized = cls._normalize(value)

            if cls._contains_phrase(normalized, phrases):
                return True

        return False

    @staticmethod
    def _metadata_values(field: BrowserField) -> tuple[str, ...]:
        """Return searchable field metadata."""

        values = (
            field.name,
            field.field_id,
            field.label,
            field.autocomplete,
            field.placeholder,
        )

        return tuple(
            value.strip()
            for value in values
            if value and value.strip()
        )

    @staticmethod
    def _normalize(value: str) -> str:
        """Normalize HTML metadata for deterministic comparison."""

        value = value.strip().lower()
        value = value.replace("-", " ")
        value = value.replace("_", " ")
        value = re.sub(r"\s+", " ", value)

        return value

    @staticmethod
    def _contains_phrase(
        text: str | None,
        phrases: tuple[str, ...],
    ) -> bool:
        """Return True when text contains a complete known phrase."""

        if not text:
            return False

        normalized_text = BrowserFieldClassifier._normalize(text)

        for phrase in phrases:
            normalized_phrase = BrowserFieldClassifier._normalize(phrase)

            if (
                normalized_text == normalized_phrase
                or f" {normalized_phrase} " in f" {normalized_text} "
            ):
                return True

        return False
