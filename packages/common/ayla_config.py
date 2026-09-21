from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AylaConfig:
    """Configuration for the public AylaGov jobs API."""

    query: str
    limit: int = 100


def parse_ayla_sources(values: list[str]) -> list[AylaConfig]:
    """Parse AylaGov source configuration strings.

    Supported formats:

        electronics
        electronics:100

    The first form uses the default page size.
    """

    configs: list[AylaConfig] = []

    for value in values:
        value = value.strip()

        if not value:
            continue

        if ":" not in value:
            query = value
            limit = 100
        else:
            query, limit_text = value.split(":", 1)

            query = query.strip()
            limit_text = limit_text.strip()

            if not query:
                continue

            try:
                limit = int(limit_text)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid Ayla limit: {limit_text!r}"
                ) from exc

        if not query:
            continue

        if not 1 <= limit <= 100:
            raise ValueError(
                "Ayla limit must be between 1 and 100."
            )

        configs.append(
            AylaConfig(
                query=query,
                limit=limit,
            )
        )

    return configs
