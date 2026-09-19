from datetime import datetime, timezone
from typing import Any

from pydantic import HttpUrl

from packages.domain.job import Job


def parse_job(data: dict[str, Any]) -> Job:
    """Convert one Himalayas job record into the internal Job model."""

    location = _parse_location(data)

    seniority = data.get("seniority")
    experience_required = _parse_seniority(seniority)

    return Job(
        title=str(data["title"]),
        company=str(data.get("companyName") or "Unknown"),
        location=location,
        description=data.get("description"),
        source="himalayas",
        source_job_id=str(data.get("guid") or data["title"]),
        source_url=HttpUrl(data["applicationLink"]),
        employment_type=(
            str(data["employmentType"])
            if data.get("employmentType")
            else None
        ),
        experience_required=experience_required,
        skills=[],
        posted_at=_parse_timestamp(data.get("pubDate")),
        discovered_at=datetime.now(timezone.utc),
    )


def _parse_location(data: dict[str, Any]) -> str | None:
    """Build a readable location from Himalayas location fields."""

    restrictions = data.get("locationRestrictions")

    if isinstance(restrictions, list) and restrictions:
        values = [
            str(value).strip()
            for value in restrictions
            if str(value).strip()
        ]

        if values:
            return ", ".join(values)

    location = data.get("location")

    if location:
        return str(location)

    return None


def _parse_seniority(value: Any) -> str | None:
    """Convert Himalayas seniority values into one canonical string."""

    if isinstance(value, list):
        values = [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

        if values:
            return ", ".join(values)

    if value:
        return str(value)

    return None


def _parse_timestamp(value: Any) -> datetime | None:
    """Convert a Unix timestamp into a timezone-aware datetime."""

    if value is None:
        return None

    return datetime.fromtimestamp(
        float(value),
        tz=timezone.utc,
    )
