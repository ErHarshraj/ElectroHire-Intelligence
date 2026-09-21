from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HopinConfig:
    """Configuration for a Hopin public job query."""

    endpoint: str
    industry: str | None = None
    location: str | None = None
    work_type: str | None = None
    role_type: str | None = None
    unofficial: bool = False


def parse_hopin_sources(values: list[str]) -> list[HopinConfig]:
    """Parse Hopin source configuration strings.

    Supported format:

        endpoint|industry|location|work_type|role_type|unofficial

    Empty fields are allowed.

    Example:

        jobs|Technology|India|||

    The endpoint must be either:
        jobs
        internships
    """
    configs: list[HopinConfig] = []

    for value in values:
        value = value.strip()

        if not value:
            continue

        parts = [part.strip() for part in value.split("|")]

        if len(parts) != 6:
            raise ValueError(
                "Invalid Hopin source configuration. "
                "Expected: endpoint|industry|location|work_type|"
                "role_type|unofficial"
            )

        (
            endpoint,
            industry,
            location,
            work_type,
            role_type,
            unofficial,
        ) = parts

        if endpoint not in {"jobs", "internships"}:
            raise ValueError(
                "Hopin endpoint must be either 'jobs' or 'internships'."
            )

        if unofficial.lower() not in {"", "true", "false"}:
            raise ValueError(
                "Hopin unofficial must be either true or false."
            )

        configs.append(
            HopinConfig(
                endpoint=endpoint,
                industry=industry or None,
                location=location or None,
                work_type=work_type or None,
                role_type=role_type or None,
                unofficial=unofficial.lower() == "true",
            )
        )

    return configs
