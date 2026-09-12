"""
Application preview assembly.

Builds a structured representation of a prepared browser application.
The preview is used for validation, auditing, and automatic execution.

This module does not submit applications.
"""

from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Page

from packages.application.browser.field_mapping import BrowserFieldMapping
from packages.application.browser.form_validator import (
    BrowserApplicationPreview,
    BrowserFormValidator,
)


@dataclass(frozen=True)
class BrowserApplicationPreviewSummary:
    """Execution-oriented summary of a prepared application."""

    url: str
    title: str
    valid: bool
    mapped_fields: int
    valid_fields: int
    invalid_fields: int
    issues: list[str]


class BrowserApplicationPreviewBuilder:
    """Build a concise preview from browser form mappings."""

    def __init__(
        self,
        validator: BrowserFormValidator | None = None,
    ) -> None:
        self._validator = validator or BrowserFormValidator()

    def build(
        self,
        page: Page,
        mappings: list[BrowserFieldMapping],
    ) -> BrowserApplicationPreviewSummary:
        """Validate mappings and build an execution summary."""

        preview: BrowserApplicationPreview = self._validator.validate(
            page,
            mappings,
        )

        valid_fields = sum(
            1
            for field in preview.fields
            if field.valid
        )

        invalid_fields = len(preview.fields) - valid_fields

        return BrowserApplicationPreviewSummary(
            url=preview.url,
            title=preview.title,
            valid=preview.valid,
            mapped_fields=len(mappings),
            valid_fields=valid_fields,
            invalid_fields=invalid_fields,
            issues=list(preview.issues),
        )
