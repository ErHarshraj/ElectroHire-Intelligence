from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FourDayWeekConfig:
    """Configuration for a 4dayweek.io job source."""

    limit: int = 100


def parse_fourdayweek_sources(
    values: list[str],
) -> list[FourDayWeekConfig]:
    """Parse 4dayweek.io source configuration strings.

    Supported format:

        limit

    Example:

        100

    The API currently supports up to 100 jobs per page.
    """

    configs: list[FourDayWeekConfig] = []

    for value in values:
        value = value.strip()

        if not value:
            continue

        try:
            limit = int(value)
        except ValueError as exc:
            raise ValueError(
                "Invalid 4dayweek source configuration. "
                "Expected an integer limit."
            ) from exc

        if not 1 <= limit <= 100:
            raise ValueError(
                "4dayweek limit must be between 1 and 100."
            )

        configs.append(FourDayWeekConfig(limit=limit))

    return configs
