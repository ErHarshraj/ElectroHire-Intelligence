from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JobicyConfig:
    """Configuration for the public Jobicy job source."""

    name: str = "jobicy"
    count: int = 200


def parse_jobicy_sources(values: list[str]) -> list[JobicyConfig]:
    """Parse Jobicy source configuration strings.

    Supported formats:
        jobicy
        jobicy:50
    """

    configs: list[JobicyConfig] = []

    for value in values:
        value = value.strip()

        if not value:
            continue

        if ":" not in value:
            configs.append(JobicyConfig(name=value))
            continue

        name, count_text = value.split(":", 1)

        name = name.strip()
        count_text = count_text.strip()

        if not name:
            continue

        try:
            count = int(count_text)
        except ValueError as exc:
            raise ValueError(
                f"Invalid Jobicy count: {count_text!r}"
            ) from exc

        if not 1 <= count <= 200:
            raise ValueError(
                "Jobicy count must be between 1 and 200."
            )

        configs.append(
            JobicyConfig(
                name=name,
                count=count,
            )
        )

    return configs
