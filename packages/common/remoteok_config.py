from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RemoteOKConfig:
    """Configuration for the public Remote OK job source."""

    name: str = "remoteok"


def parse_remoteok_sources(
    values: list[str],
) -> list[RemoteOKConfig]:
    """Parse Remote OK source configuration strings."""

    configs: list[RemoteOKConfig] = []

    for value in values:
        value = value.strip()

        if not value:
            continue

        configs.append(
            RemoteOKConfig(name=value)

        )

    return configs
