from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkdayConfig:
    """Configuration for a public Workday career board."""

    tenant: str
    base_url: str
    site: str
    company_name: str
    batches: int = 1


def parse_workday_sources(values: list[str]) -> list[WorkdayConfig]:
    """Parse Workday source configurations.

    Supported format:

        tenant|base_url|site|company_name|batches

    Example:

        analogdevices|https://analogdevices.wd1.myworkdayjobs.com|External|Analog Devices|10
    """
    configs: list[WorkdayConfig] = []

    for value in values:
        value = value.strip()
        if not value:
            continue

        parts = [part.strip() for part in value.split("|")]

        if len(parts) != 5:
            raise ValueError(
                "Invalid Workday source configuration. "
                "Expected: tenant|base_url|site|company_name|batches"
            )

        tenant, base_url, site, company_name, batches_text = parts

        if not tenant or not base_url or not site or not company_name:
            raise ValueError(
                "Workday tenant, base URL, site, and company name "
                "must not be empty."
            )

        if not base_url.startswith(("http://", "https://")):
            raise ValueError(
                f"Invalid Workday base URL: {base_url!r}"
            )

        try:
            batches = int(batches_text)
        except ValueError as exc:
            raise ValueError(
                f"Invalid Workday batch count: {batches_text!r}"
            ) from exc

        if not 1 <= batches <= 100:
            raise ValueError(
                "Workday batch count must be between 1 and 100."
            )

        configs.append(
            WorkdayConfig(
                tenant=tenant,
                base_url=base_url.rstrip("/"),
                site=site,
                company_name=company_name,
                batches=batches,
            )
        )

    return configs
