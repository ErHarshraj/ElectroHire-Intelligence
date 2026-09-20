from datetime import datetime, timezone
from typing import Any

from pydantic import HttpUrl

from packages.domain.job import Job


def parse_job(data: dict[str, Any]) -> Job:
    """Convert a Jobicy API record into the ElectroHire Job model."""
    return Job(
        title=str(data["jobTitle"]),
        company=str(data.get("companyName") or "Unknown"),
        location=_parse_location(data),
        description=data.get("jobDescription"),
        source="jobicy",
        source_job_id=str(data["id"]),
        source_url=HttpUrl(
            data.get("url")
            or f"https://jobicy.com/jobs/{data['id']}"
        ),
        employment_type=_parse_job_type(data),
        experience_required=_parse_job_level(data),
        skills=_parse_skills(data),
        posted_at=_parse_timestamp(data),
        discovered_at=datetime.now(timezone.utc),
    )


def _parse_location(data: dict[str, Any]) -> str | None:
    location = data.get("jobGeo")

    if not location:
        return None

    return str(location).strip() or None


def _parse_job_type(data: dict[str, Any]) -> str | None:
    values = data.get("jobType")

    if not isinstance(values, list):
        return None

    cleaned = [
        str(value).strip()
        for value in values
        if str(value).strip()
    ]

    return ", ".join(cleaned) if cleaned else None


def _parse_job_level(data: dict[str, Any]) -> str | None:
    value = data.get("jobLevel")

    if not value:
        return None

    return str(value).strip() or None


def _parse_skills(data: dict[str, Any]) -> list[str]:
    values = data.get("jobIndustry")

    if not isinstance(values, list):
        return []

    return [
        str(value).strip()
        for value in values
        if str(value).strip()
    ]


def _parse_timestamp(data: dict[str, Any]) -> datetime | None:
    value = data.get("pubDate")

    if not value:
        return None

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(
            float(value),
            tz=timezone.utc,
        )

    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except ValueError:
        return None
