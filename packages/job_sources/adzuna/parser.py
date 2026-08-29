from datetime import datetime, timezone
from typing import Any

from pydantic import HttpUrl

from packages.domain.job import Job


def parse_job(data: dict[str, Any]) -> Job:
    """Convert one Adzuna job record into the internal Job model."""

    return Job(
        title=str(data["title"]),
        company=str(data["company"]["display_name"]),
        location=(
            data.get("location", {}).get("display_name")
            if data.get("location")
            else None
        ),
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
