from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HimalayasConfig:
    """Configuration for one Himalayas job source."""

    name: str
    limit: int = 50


def parse_himalayas_sources(
    values: list[str],
) -> list[HimalayasConfig]:
    """Parse Himalayas source configuration strings.

    Format:

        name
        name:limit
    """

    configs: list[HimalayasConfig] = []

    for value in values:
        value = value.strip()

        if not value:
            continue

        parts = [part.strip() for part in value.split(":")]

        name = parts[0]

        if not name:
            raise ValueError(
                "Himalayas source name must not be empty."
            )

        limit = 50

        if len(parts) > 1:
            try:
                limit = int(parts[1])
            except ValueError as exc:
                raise ValueError(
                    f"Invalid Himalayas limit: {parts[1]!r}"
                ) from exc

        if limit <= 0:
            raise ValueError(
                "Himalayas limit must be greater than zero."
            )

        configs.append(
            HimalayasConfig(
                name=name,
                limit=limit,
            )
        )

    return configs
