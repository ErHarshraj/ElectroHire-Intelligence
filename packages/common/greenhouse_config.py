"""
Greenhouse career-board configuration parsing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GreenhouseBoardConfig:
    """Configuration for one company's public Greenhouse job board."""

    company_name: str
    board_token: str


def parse_greenhouse_boards(
    boards: list[str],
) -> list[GreenhouseBoardConfig]:
    """
    Parse configured Greenhouse boards.

    Expected format:
        "Company Name:board-token"

    Returns one GreenhouseBoardConfig for each valid entry.
    """

    parsed: list[GreenhouseBoardConfig] = []

    for entry in boards:
        if not isinstance(entry, str):
            raise TypeError("Greenhouse board configuration must be a string.")

        value = entry.strip()

        if not value:
            raise ValueError(
                "Greenhouse board configuration must not be empty."
            )

        if value.count(":") != 1:
            raise ValueError(
                "Greenhouse board configuration must use "
                "'Company Name:board-token' format."
            )

        company_name, board_token = (
            part.strip()
            for part in value.split(":", 1)
        )

        if not company_name:
            raise ValueError(
                "Greenhouse board company name must not be empty."
            )

        if not board_token:
            raise ValueError(
                "Greenhouse board token must not be empty."
            )

        parsed.append(
            GreenhouseBoardConfig(
                company_name=company_name,
                board_token=board_token,
            )
        )

    return parsed
