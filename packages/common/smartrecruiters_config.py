"""
Configuration parsing for SmartRecruiters public career boards.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SmartRecruitersBoardConfig:
    """Configuration for one SmartRecruiters public career board."""

    company_name: str
    company_identifier: str


def parse_smartrecruiters_boards(
    boards: list[str],
) -> list[SmartRecruitersBoardConfig]:
    """
    Parse SmartRecruiters board configuration entries.

    Expected format:
        Company Name:company-identifier
    """

    configs: list[SmartRecruitersBoardConfig] = []

    for raw_board in boards:
        value = raw_board.strip()

        if not value:
            raise ValueError(
                "SmartRecruiters board configuration must not be empty."
            )

        if ":" not in value:
            raise ValueError(
                "Invalid SmartRecruiters board configuration. "
                "Expected format: Company Name:company-identifier"
            )

        company_name, company_identifier = value.split(":", 1)

        company_name = company_name.strip()
        company_identifier = company_identifier.strip()

        if not company_name:
            raise ValueError(
                "SmartRecruiters company name must not be empty."
            )

        if not company_identifier:
            raise ValueError(
                "SmartRecruiters company identifier must not be empty."
            )

        configs.append(
            SmartRecruitersBoardConfig(
                company_name=company_name,
                company_identifier=company_identifier,
            )
        )

    return configs
