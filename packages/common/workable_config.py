from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkableConfig:
    """Configuration for a public Workable career account."""

    account_slug: str
    company_name: str


def parse_workable_sources(values: list[str]) -> list[WorkableConfig]:
    """Parse Workable source configuration strings.

    Supported format:
        account_slug|company_name

    Example:
        trocaire|Trócaire
    """
    configs: list[WorkableConfig] = []

    for value in values:
        value = value.strip()
        if not value:
            continue

        parts = [part.strip() for part in value.split("|")]

        if len(parts) != 2:
            raise ValueError(
                "Invalid Workable source configuration. "
                "Expected: account_slug|company_name"
            )

        account_slug, company_name = parts

        if not account_slug or not company_name:
            raise ValueError(
                "Workable account slug and company name must not be empty."
            )

        configs.append(
            WorkableConfig(
                account_slug=account_slug,
                company_name=company_name,
            )
        )

    return configs
