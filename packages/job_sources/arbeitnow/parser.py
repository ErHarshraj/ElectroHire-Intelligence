from datetime import datetime, timezone
from typing import Any

from pydantic import HttpUrl

from packages.domain.job import Job

_EXPERIENCE_LEVELS = {
    "entry",
    "junior",
    "mid",
    "middle",
    "senior",
    "lead",
    "manager",
    "executive",
}


def parse_job(data: dict[str, Any]) -> Job:
    """Convert an Arbeitnow API record into the ElectroHire Job model."""
    job_types = _clean_list(data.get("job_types"))

    return Job(
        title=str(data["title"]),
        company=str(data.get("company_name") or "Unknown"),
        location=_parse_location(data),
        description=data.get("description"),
        source="arbeitnow",
        source_job_id=str(data["slug"]),
        source_url=HttpUrl(data["url"]),
        employment_type=_parse_employment_type(job_types),
        experience_required=_parse_experience(job_types),
        skills=_clean_list(data.get("tags")),
        posted_at=_parse_timestamp(data.get("created_at")),
        discovered_at=datetime.now(timezone.utc),
    )


def _parse_location(data: dict[str, Any]) -> str | None:
    value = data.get("location")

    if not value:
        return None

    return str(value).strip() or None


def _clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    return [
        str(item).strip()
        for item in value
        if str(item).strip()
    ]


def _parse_employment_type(values: list[str]) -> str | None:
    employment_values = [
        value
        for value in values
        if value.lower() not in _EXPERIENCE_LEVELS
    ]

    return ", ".join(employment_values) or None


def _parse_experience(values: list[str]) -> str | None:
    experience_values = [
        value
        for value in values
        if value.lower() in _EXPERIENCE_LEVELS
    ]

    return ", ".join(experience_values) or None


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(
                float(value),
                tz=timezone.utc,
            )
        except (OverflowError, OSError, ValueError):
            return None

    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except ValueError:
        return None
