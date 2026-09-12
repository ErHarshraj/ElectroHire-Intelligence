"""
Map classified browser fields to candidate profile data.

This module is deterministic and does not interact with the browser.
It does not fill fields and does not submit forms.
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.application.browser.field_classifier import (
    BrowserFieldClassification,
    BrowserFieldKind,
)
from packages.application.profile import CandidateProfile


@dataclass(frozen=True)
class BrowserFieldMapping:
    """Mapping between a browser field and candidate-profile data."""

    field: BrowserFieldClassification
    value: str | None
    source: str | None
    mappable: bool
    reason: str


class BrowserFieldMapper:
    """
    Map classified browser fields to CandidateProfile values.

    Only fields with an explicit, deterministic profile mapping are mapped.
    Unknown fields remain unmapped.
    """

    def map(
        self,
        classification: BrowserFieldClassification,
        profile: CandidateProfile,
    ) -> BrowserFieldMapping:
        """Map one classified browser field."""

        kind = classification.kind

        if kind == BrowserFieldKind.FULL_NAME:
            return self._mapped(
                classification,
                profile.full_name,
                "full_name",
                "mapped to candidate full name",
            )

        if kind == BrowserFieldKind.EMAIL:
            return self._mapped(
                classification,
                profile.email,
                "email",
                "mapped to candidate email",
            )

        if kind == BrowserFieldKind.PHONE:
            return self._mapped(
                classification,
                profile.phone,
                "phone",
                "mapped to candidate phone",
            )

        if kind == BrowserFieldKind.RESUME:
            return self._mapped(
                classification,
                profile.resume_path,
                "resume_path",
                "mapped to candidate resume path",
            )

        if kind == BrowserFieldKind.COVER_LETTER:
            return BrowserFieldMapping(
                field=classification,
                value=None,
                source="generated_cover_letter",
                mappable=False,
                reason="cover letter requires generated application content",
            )

        if kind == BrowserFieldKind.EXPERIENCE_LEVEL:
            return self._mapped(
                classification,
                profile.application_answers.get("experience_level"),
                "application_answers.experience_level",
                "mapped from candidate application answers",
            )

        if kind == BrowserFieldKind.SUBMIT:
            return BrowserFieldMapping(
                field=classification,
                value=None,
                source=None,
                mappable=False,
                reason="submit controls are never mapped to candidate data",
            )

        return BrowserFieldMapping(
            field=classification,
            value=None,
            source=None,
            mappable=False,
            reason="unknown browser field has no deterministic profile mapping",
        )

    def map_all(
        self,
        classifications: list[BrowserFieldClassification],
        profile: CandidateProfile,
    ) -> list[BrowserFieldMapping]:
        """Map every classified browser field."""

        return [
            self.map(classification, profile)
            for classification in classifications
        ]

    @staticmethod
    def _mapped(
        classification: BrowserFieldClassification,
        value: str | None,
        source: str,
        reason: str,
    ) -> BrowserFieldMapping:
        """Build a mapping result while requiring an actual value."""

        if value:
            return BrowserFieldMapping(
                field=classification,
                value=value,
                source=source,
                mappable=True,
                reason=reason,
            )

        return BrowserFieldMapping(
            field=classification,
            value=None,
            source=source,
            mappable=False,
            reason=f"{reason}; candidate value is missing",
        )
