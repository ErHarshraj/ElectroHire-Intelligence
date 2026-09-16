"""
Configuration parsing for Ashby public career boards.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AshbyBoardConfig:
    """Configuration for one Ashby public job board."""

    company_name: str
    board_name: str


def parse_ashby_boards(
    boards: list[str],
) -> list[AshbyBoardConfig]:
    """
    Parse Ashby board configuration entries.

    Expected format:
        Company Name:board-name
    """

    configs: list[AshbyBoardConfig] = []

    for raw_board in boards:
        value = raw_board.strip()

        if not value:
            raise ValueError(
                "Ashby board configuration must not be empty."
            )

        if ":" not in value:
            raise ValueError(
                "Invalid Ashby board configuration. "
                "Expected format: Company Name:board-name"
            )

        company_name, board_name = value.split(":", 1)

        company_name = company_name.strip()
        board_name = board_name.strip()

        if not company_name:
            raise ValueError(
                "Ashby company name must not be empty."
            )

        if not board_name:
            raise ValueError(
                "Ashby board name must not be empty."
            )

        configs.append(
            AshbyBoardConfig(
                company_name=company_name,
                board_name=board_name,
            )
        )

    return configs
