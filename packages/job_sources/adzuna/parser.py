from datetime import datetime, timezone
from typing import Any

from pydantic import HttpUrl

from packages.domain.job import Job


def parse_job(data: dict[str, Any]) -> Job:
    """Convert one Adzuna job record into the internal Job model."""

    company = data.get("company")
    company_name = (
        company.get("display_name")
        if isinstance(company, dict)
        else None
    )

    location = data.get("location")
    location_name = (
        location.get("display_name")
        if isinstance(location, dict)
        else None
    )

    return Job(
        title=str(data["title"]),
        company=str(company_name) if company_name else "Unknown",
        location=location_name,
        description=data.get("description"),
        source="adzuna",
        source_job_id=str(data["id"]),
        source_url=HttpUrl(data["redirect_url"]),
        employment_type=None,
        experience_required=None,
        skills=[],
        posted_at=_parse_date(data.get("created")),
        discovered_at=datetime.now(timezone.utc),
    )


def _parse_date(value: str | None) -> datetime | None:
    """Parse an Adzuna timestamp into a timezone-aware datetime."""

    if value is None:
        return None

    return datetime.fromisoformat(
        value.replace("Z", "+00:00"),
    )
