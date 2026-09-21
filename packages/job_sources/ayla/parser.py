from datetime import datetime, timezone
from typing import Any

from pydantic import HttpUrl

from packages.domain.job import Job


def parse_job(data: dict[str, Any]) -> Job:
    """Convert an AylaGov API record into the ElectroHire Job model."""
    return Job(
        title=str(data["title"]),
        company=str(
            data.get("agency")
            or data.get("organizationName")
            or "Unknown"
        ),
        location=_parse_location(data),
        description=_parse_description(data),
        source="ayla",
        source_job_id=str(data["id"]),
        source_url=HttpUrl(data["sourceUrl"]),
        employment_type=_parse_text(
            data.get("employmentType")
            or data.get("jobType")
        ),
        experience_required=_parse_experience(data),
        skills=_parse_skills(data),
        posted_at=_parse_timestamp(data),
        discovered_at=datetime.now(timezone.utc),
    )


def _parse_location(data: dict[str, Any]) -> str | None:
    for field in (
        "primaryLocationText",
        "location",
    ):
        value = data.get(field)

        if isinstance(value, str) and value.strip():
            return value.strip()

    parts = [
        str(data.get(field)).strip()
        for field in ("city", "state", "countryCode")
        if data.get(field)
    ]

    location = ", ".join(parts)

    return location or None


def _parse_description(data: dict[str, Any]) -> str | None:
    for field in ("description", "rawJobDescription"):
        value = data.get(field)

        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _parse_text(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    return text or None


def _parse_experience(data: dict[str, Any]) -> str | None:
    value = (
        data.get("seniorityLevel")
        or data.get("seniorityDisplay")
        or data.get("experience")
    )

    if isinstance(value, dict):
        minimum = value.get("min")
        maximum = value.get("max")

        if minimum is not None or maximum is not None:
            parts = [
                str(item)
                for item in (minimum, maximum)
                if item is not None
            ]

            return "-".join(parts)

        return None

    return _parse_text(value)


def _parse_skills(data: dict[str, Any]) -> list[str]:
    skills: list[str] = []

    for field in (
        "skills",
        "mustHaveSkills",
        "preferredSkills",
    ):
        values = data.get(field)

        if isinstance(values, str):
            values = [values]

        if not isinstance(values, list):
            continue

        for value in values:
            if isinstance(value, dict):
                name = (
                    value.get("name")
                    or value.get("skill")
                    or value.get("title")
                )
            else:
                name = value

            if name is None:
                continue

            cleaned = str(name).strip()

            if cleaned and cleaned not in skills:
                skills.append(cleaned)

    return skills


def _parse_timestamp(data: dict[str, Any]) -> datetime | None:
    value = data.get("postedDate")

    if not value:
        return None

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(
            float(value),
            tz=timezone.utc,
        )

    try:
        timestamp = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except ValueError:
        return None

    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)

    return timestamp
