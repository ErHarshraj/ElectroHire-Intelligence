"""
Browser form field inspection.

This module only observes form structure.
It does not fill fields and does not submit forms.
"""

from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Locator, Page


@dataclass(frozen=True)
class BrowserField:
    """Structured metadata describing one form field."""

    element: str
    field_type: str
    name: str | None
    field_id: str | None
    label: str | None
    autocomplete: str | None
    required: bool
    placeholder: str | None
    value: str | None


class BrowserFieldInspector:
    """Inspect application-form fields without modifying the page."""

    def inspect(self, page: Page) -> list[BrowserField]:
        """Return structured metadata for form controls on the page."""
        fields: list[BrowserField] = []

        fields.extend(self._inspect_inputs(page.locator("input")))
        fields.extend(self._inspect_textareas(page.locator("textarea")))
        fields.extend(self._inspect_selects(page.locator("select")))
        fields.extend(self._inspect_buttons(page.locator("button")))

        return fields

    def _inspect_inputs(self, locator: Locator) -> list[BrowserField]:
        fields: list[BrowserField] = []

        for index in range(locator.count()):
            element = locator.nth(index)

            field_type = element.get_attribute("type") or "text"

            fields.append(
                BrowserField(
                    element="input",
                    field_type=field_type,
                    name=element.get_attribute("name"),
                    field_id=element.get_attribute("id"),
                    label=self._get_label(element),
                    autocomplete=element.get_attribute("autocomplete"),
                    required=element.get_attribute("required") is not None,
                    placeholder=element.get_attribute("placeholder"),
                    value=element.get_attribute("value"),
                )
            )

        return fields

    def _inspect_textareas(self, locator: Locator) -> list[BrowserField]:
        fields: list[BrowserField] = []

        for index in range(locator.count()):
            element = locator.nth(index)

            fields.append(
                BrowserField(
                    element="textarea",
                    field_type="textarea",
                    name=element.get_attribute("name"),
                    field_id=element.get_attribute("id"),
                    label=self._get_label(element),
                    autocomplete=element.get_attribute("autocomplete"),
                    required=element.get_attribute("required") is not None,
                    placeholder=element.get_attribute("placeholder"),
                    value=element.input_value(),
                )
            )

        return fields

    def _inspect_selects(self, locator: Locator) -> list[BrowserField]:
        fields: list[BrowserField] = []

        for index in range(locator.count()):
            element = locator.nth(index)

            fields.append(
                BrowserField(
                    element="select",
                    field_type="select",
                    name=element.get_attribute("name"),
                    field_id=element.get_attribute("id"),
                    label=self._get_label(element),
                    autocomplete=element.get_attribute("autocomplete"),
                    required=element.get_attribute("required") is not None,
                    placeholder=None,
                    value=element.input_value(),
                )
            )

        return fields

    def _inspect_buttons(self, locator: Locator) -> list[BrowserField]:
        fields: list[BrowserField] = []

        for index in range(locator.count()):
            element = locator.nth(index)

            button_type = element.get_attribute("type") or "submit"

            fields.append(
                BrowserField(
                    element="button",
                    field_type=button_type,
                    name=element.get_attribute("name"),
                    field_id=element.get_attribute("id"),
                    label=element.inner_text().strip() or None,
                    autocomplete=None,
                    required=False,
                    placeholder=None,
                    value=element.get_attribute("value"),
                )
            )

        return fields

    @staticmethod
    def _get_label(element: Locator) -> str | None:
        """Resolve the label associated with a form control."""
        field_id = element.get_attribute("id")

        if field_id:
            label = element.locator(
                f"xpath=preceding::label[@for='{field_id}'][1]"
            )

            if label.count() > 0:
                text = label.inner_text().strip()
                if text:
                    return text

        parent_label = element.locator("xpath=ancestor::label[1]")

        if parent_label.count() > 0:
            text = parent_label.inner_text().strip()
            if text:
                return text

        return None
