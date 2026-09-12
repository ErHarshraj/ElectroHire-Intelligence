"""
Browser application form validation and preview.

This module validates a prepared application form without submitting it.
It never clicks a submit button and never calls form submission APIs.
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
class BrowserFieldValidation:
    """Validation result for one mapped browser field."""

    field: BrowserFieldClassification
    value: str | None
    valid: bool
    message: str


@dataclass(frozen=True)
class BrowserApplicationPreview:
    """Human-readable validation preview before submission."""

    url: str
    title: str
    valid: bool
    fields: list[BrowserFieldValidation]
    issues: list[str]


class BrowserFormValidator:
    """Validate a prepared browser application without submitting it."""

    NON_DATA_KINDS = {
        BrowserFieldKind.COVER_LETTER,
        BrowserFieldKind.SUBMIT,
    }

    def validate(
        self,
        page: Page,
        mappings: list[BrowserFieldMapping],
    ) -> BrowserApplicationPreview:
        """Validate mapped candidate fields and required form controls."""

        fields = [
            self._validate_mapping(page, mapping)
            for mapping in mappings
        ]

        issues = [
            result.message
            for result in fields
            if not result.valid
        ]

        issues.extend(
            self._find_unmapped_required_fields(page, mappings)
        )

        return BrowserApplicationPreview(
            url=page.url,
            title=page.title(),
            valid=not issues,
            fields=fields,
            issues=issues,
        )

    def _validate_mapping(
        self,
        page: Page,
        mapping: BrowserFieldMapping,
    ) -> BrowserFieldValidation:
        classification = mapping.field
        kind = classification.kind

        # These are controls/content handled by another stage.
        # They are not candidate-data validation failures.
        if kind == BrowserFieldKind.SUBMIT:
            return BrowserFieldValidation(
                field=classification,
                value=None,
                valid=True,
                message="submit control is handled by submission executor",
            )

        if kind == BrowserFieldKind.COVER_LETTER:
            return BrowserFieldValidation(
                field=classification,
                value=None,
                valid=True,
                message="cover letter is optional and not generated automatically",
            )

        if kind == BrowserFieldKind.UNKNOWN:
            return BrowserFieldValidation(
                field=classification,
                value=mapping.value,
                valid=False,
                message="unknown field cannot be validated automatically",
            )

        if not mapping.mappable:
            return BrowserFieldValidation(
                field=classification,
                value=mapping.value,
                valid=False,
                message=f"field is not mappable: {mapping.reason}",
            )

        if mapping.value is None or not mapping.value.strip():
            return BrowserFieldValidation(
                field=classification,
                value=mapping.value,
                valid=False,
                message="mapped field has no candidate value",
            )

        try:
            locator = self._resolve_locator(page, classification)
            self._validate_value(locator, kind, mapping.value)

        except Exception as exc:
            return BrowserFieldValidation(
                field=classification,
                value=mapping.value,
                valid=False,
                message=f"field validation failed: {type(exc).__name__}: {exc}",
            )

        return BrowserFieldValidation(
            field=classification,
            value=mapping.value,
            valid=True,
            message=f"field is valid from {mapping.source}",
        )

    @staticmethod
    def _resolve_locator(
        page: Page,
        classification: BrowserFieldClassification,
    ) -> Locator:
        """Resolve exactly one form control."""

        field = classification.field

        if field.field_id:
            locator = page.locator(f"#{field.field_id}")
        elif field.name:
            locator = page.locator(
                f'{field.element}[name="{field.name}"]'
            )
        else:
            raise ValueError(
                "field has neither an id nor a name"
            )

        count = locator.count()

        if count != 1:
            raise ValueError(
                f"expected exactly one field target, found {count}"
            )

        return locator

    @classmethod
    def _validate_value(
        cls,
        locator: Locator,
        kind: BrowserFieldKind,
        expected_value: str,
    ) -> None:
        """Validate the current browser value without changing it."""

        if kind == BrowserFieldKind.RESUME:
            cls._validate_resume(locator, expected_value)
            return

        if kind == BrowserFieldKind.EXPERIENCE_LEVEL:
            cls._validate_select(locator, expected_value)
            return

        actual_value = locator.input_value()

        if actual_value != expected_value:
            raise ValueError(
                f"expected {expected_value!r}, got {actual_value!r}"
            )

    @staticmethod
    def _validate_resume(
        locator: Locator,
        expected_value: str,
    ) -> None:
        """Verify that the expected resume file is attached."""

        files = locator.evaluate(
            """element => Array.from(element.files || []).map(
                file => file.name
            )"""
        )

        expected_name = Path(expected_value).name

        if files != [expected_name]:
            raise ValueError(
                f"expected resume {expected_name!r}, got {files!r}"
            )

    @staticmethod
    def _validate_select(
        locator: Locator,
        expected_value: str,
    ) -> None:
        """Verify that the selected option matches the mapping."""

        options = locator.locator("option").all()

        available_values = {
            option.get_attribute("value") or ""
            for option in options
        }

        if expected_value not in available_values:
            raise ValueError(
                f"select option {expected_value!r} is not available"
            )

        actual_value = locator.input_value()

        if actual_value != expected_value:
            raise ValueError(
                f"expected selected value {expected_value!r}, "
                f"got {actual_value!r}"
            )

    @staticmethod
    def _find_unmapped_required_fields(
        page: Page,
        mappings: list[BrowserFieldMapping],
    ) -> list[str]:
        """Find required candidate-data controls absent from the mapping."""

        mapped_keys = {
            BrowserFormValidator._field_key(mapping.field)
            for mapping in mappings
            if mapping.field.kind not in BrowserFormValidator.NON_DATA_KINDS
        }

        issues: list[str] = []

        controls = page.locator(
            "input[required], textarea[required], select[required]"
        ).all()

        for control in controls:
            element = control.evaluate(
                "element => element.tagName.toLowerCase()"
            )
            field_id = control.get_attribute("id")
            name = control.get_attribute("name")

            key = (element, field_id, name)

            if key in mapped_keys:
                continue

            label = BrowserFormValidator._label_for_control(
                page,
                control,
                field_id,
            )

            description = label or field_id or name or element

            issues.append(
                f"required field is not mapped: {description}"
            )

        return issues

    @staticmethod
    def _field_key(
        classification: BrowserFieldClassification,
    ) -> tuple[str, str | None, str | None]:
        field = classification.field

        return (
            field.element,
            field.field_id,
            field.name,
        )

    @staticmethod
    def _label_for_control(
        page: Page,
        control: Locator,
        field_id: str | None,
    ) -> str | None:
        """Resolve a readable label for an unmapped required field."""

        if field_id:
            label = page.locator(
                f'label[for="{field_id}"]'
            )

            if label.count() == 1:
                text = label.inner_text().strip()

                if text:
                    return text

        parent_label = control.locator(
            "xpath=ancestor::label[1]"
        )

        if parent_label.count() == 1:
            text = parent_label.inner_text().strip()

            if text:
                return text

        return None
