from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArbeitnowConfig:
    """Configuration for the public Arbeitnow job source."""

    name: str = "arbeitnow"
    pages: int = 1


def parse_arbeitnow_sources(values: list[str]) -> list[ArbeitnowConfig]:
    """Parse Arbeitnow source configuration strings.

    Supported formats:
        arbeitnow
        arbeitnow:3
    """

    configs: list[ArbeitnowConfig] = []

    for value in values:
        value = value.strip()

        if not value:
            continue

        if ":" not in value:
            configs.append(ArbeitnowConfig(name=value))
            continue

        name, pages_text = value.split(":", 1)

        name = name.strip()
        pages_text = pages_text.strip()

        if not name:
            continue

        try:
            pages = int(pages_text)
        except ValueError as exc:
            raise ValueError(
                f"Invalid Arbeitnow page count: {pages_text!r}"
            ) from exc

        if not 1 <= pages <= 20:
            raise ValueError(
                "Arbeitnow page count must be between 1 and 20."
            )

        configs.append(
            ArbeitnowConfig(
                name=name,
                pages=pages,
            )
        )

    return configs
