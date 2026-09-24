from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RipplingConfig:
    """Configuration for a public Rippling career board."""

    board_slug: str
    company_name: str


def parse_rippling_sources(values: list[str]) -> list[RipplingConfig]:
    """Parse Rippling source configuration strings.

    Supported format:
        board_slug|company_name

    Example:
        tylsemi|TYLsemi, Inc.
    """
    configs: list[RipplingConfig] = []

    for value in values:
        value = value.strip()
        if not value:
            continue

        parts = [part.strip() for part in value.split("|")]

        if len(parts) != 2:
            raise ValueError(
                "Invalid Rippling source configuration. Expected: board_slug|company_name"
            )

        board_slug, company_name = parts

        if not board_slug or not company_name:
            raise ValueError("Rippling board slug and company name must not be empty.")

        configs.append(
            RipplingConfig(
                board_slug=board_slug,
                company_name=company_name,
            )
        )

    return configs
