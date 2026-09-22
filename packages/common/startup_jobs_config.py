from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StartupJobsConfig:
    """Configuration for a Startup Jobs RSS role feed."""

    role: str


def parse_startup_jobs_sources(
    values: list[str],
) -> list[StartupJobsConfig]:
    """Parse Startup Jobs role-feed configuration strings.

    Supported format:

        hardware-engineer
        embedded-engineer
    """

    configs: list[StartupJobsConfig] = []

    for value in values:
        role = value.strip()

        if not role:
            continue

        configs.append(
            StartupJobsConfig(role=role)
        )

    return configs
