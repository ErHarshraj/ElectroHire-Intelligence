"""
Lever public career-board configuration parsing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LeverBoardConfig:
    """Configuration for one company's public Lever job board."""

    company_name: str
    site: str


def parse_lever_boards(
    boards: list[str],
) -> list[LeverBoardConfig]:
    """
    Parse configured Lever boards.

    Expected format:
        "Company Name:site"

    Example:
        "Palantir:palantir"
    """

    parsed: list[LeverBoardConfig] = []

    for entry in boards:
        if not isinstance(entry, str):
            raise TypeError("Lever board configuration must be a string.")

        value = entry.strip()

        if not value:
            raise ValueError(
                "Lever board configuration must not be empty."
            )

        if value.count(":") != 1:
            raise ValueError(
                "Lever board configuration must use "
                "'Company Name:site' format."
            )

        company_name, site = (
            part.strip()
            for part in value.split(":", 1)
        )

        if not company_name:
            raise ValueError(
                "Lever board company name must not be empty."
            )

        if not site:
            raise ValueError(
                "Lever board site must not be empty."
            )

        parsed.append(
            LeverBoardConfig(
                company_name=company_name,
                site=site,
            )
        )

    return parsed
