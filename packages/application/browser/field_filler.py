"""
Controlled browser field filling.

This module fills only explicitly mapped candidate fields.
It never clicks submit and never submits an application.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Locator, Page

from packages.application.browser.field_classifier import (
    BrowserFieldClassification,
    BrowserFieldKind,
)
from packages.application.browser.field_mapping import BrowserFieldMapping


@dataclass(frozen=True)
class BrowserFieldFillResult:
    field: BrowserFieldClassification
    success: bool
    message: str


class BrowserFieldFiller:
    """Safely fill and verify approved browser application fields."""

    ALLOWED_KINDS = {
        BrowserFieldKind.FULL_NAME,
        BrowserFieldKind.EMAIL,
        BrowserFieldKind.PHONE,
        BrowserFieldKind.RESUME,
        BrowserFieldKind.EXPERIENCE_LEVEL,
    }

    def fill(
        self,
        page: Page,
        mapping: BrowserFieldMapping,
    ) -> BrowserFieldFillResult:
        """Fill one approved field and verify the resulting browser value."""

        classification = mapping.field
        kind = classification.kind

        if kind not in self.ALLOWED_KINDS:
            return BrowserFieldFillResult(
                field=classification,
                success=False,
                message=f"field kind {kind.value!r} is not allowed for filling",
            )

        if not mapping.mappable:
            return BrowserFieldFillResult(
                field=classification,
                success=False,
                message=f"field is not mappable: {mapping.reason}",
            )

        if mapping.value is None or not mapping.value.strip():
            return BrowserFieldFillResult(
                field=classification,
                success=False,
                message="mapped field has no candidate value",
            )

        try:
            locator = self._resolve_locator(page, classification)

            if kind == BrowserFieldKind.RESUME:
                self._fill_resume(locator, mapping.value)
            elif kind == BrowserFieldKind.EXPERIENCE_LEVEL:
                self._fill_select(locator, mapping.value)
            else:
                locator.fill(mapping.value)

            self._verify(locator, kind, mapping.value)

            return BrowserFieldFillResult(
                field=classification,
                success=True,
                message=f"field filled and verified from {mapping.source}",
            )

        except Exception as exc:
            return BrowserFieldFillResult(
                field=classification,
                success=False,
                message=f"field fill failed: {type(exc).__name__}: {exc}",
            )

    def fill_all(
        self,
        page: Page,
        mappings: list[BrowserFieldMapping],
    ) -> list[BrowserFieldFillResult]:
        """Fill mappings in order and return one result per mapping."""

        return [self.fill(page, mapping) for mapping in mappings]

    @staticmethod
    def _resolve_locator(
        page: Page,
        classification: BrowserFieldClassification,
    ) -> Locator:
        """Resolve exactly one form control using stable metadata."""

        field = classification.field

        if field.field_id:
            locator = page.locator(f"#{field.field_id}")
        elif field.name:
            locator = page.locator(
                f'{field.element}[name="{field.name}"]'
            )
        else:
            raise ValueError(
                "field has neither an id nor a name and cannot be "
                "safely targeted"
            )

        count = locator.count()

        if count != 1:
            raise ValueError(
                f"expected exactly one field target, found {count}"
            )

        return locator

    @staticmethod
    def _fill_resume(locator: Locator, value: str) -> None:
        """Attach the candidate resume file to a file input."""

        path = Path(value).expanduser()

        if not path.is_file():
            raise FileNotFoundError(
                f"candidate resume file does not exist: {path}"
            )

        locator.set_input_files(str(path))

    @staticmethod
    def _fill_select(locator: Locator, value: str) -> None:
        """Select an existing option without inventing form values."""

        options = locator.locator("option").all()

        available_values = {
            option.get_attribute("value") or ""
            for option in options
        }

        if value not in available_values:
            raise ValueError(
                f"select option {value!r} is not available"
            )

        locator.select_option(value=value)

    @staticmethod
    def _verify(
        locator: Locator,
        kind: BrowserFieldKind,
        expected_value: str,
    ) -> None:
        """Verify that the browser contains the intended value."""

        if kind == BrowserFieldKind.RESUME:
            files = locator.locator("xpath=.").evaluate(
                """element => Array.from(element.files || []).map(
                    file => file.name
                )"""
            )

            expected_name = Path(expected_value).name

            if files != [expected_name]:
                raise ValueError(
                    f"resume verification failed: expected "
                    f"{expected_name!r}, got {files!r}"
                )

            return

        actual_value = locator.input_value()

        if actual_value != expected_value:
            raise ValueError(
                f"value verification failed: expected "
                f"{expected_value!r}, got {actual_value!r}"
            )
