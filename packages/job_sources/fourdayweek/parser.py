from datetime import datetime, timezone
from typing import Any

from pydantic import HttpUrl

from packages.domain.job import Job


def parse_job(data: dict[str, Any]) -> Job:
    """Convert a 4dayweek.io API record into the ElectroHire Job model."""
    company = data.get("company")
    company_name = (
        company.get("name")
        if isinstance(company, dict)
        else None
    )

    return Job(
        title=str(data["title"]),
        company=str(company_name or "Unknown"),
        location=_parse_location(data),
        description=data.get("description"),
        source="fourdayweek",
        source_job_id=str(data["id"]),
        source_url=HttpUrl(data["url"]),
        employment_type=_parse_text(data.get("contract_type")),
        experience_required=_parse_text(data.get("level")),
        skills=_parse_skills(data),
        posted_at=_parse_timestamp(data),
        discovered_at=datetime.now(timezone.utc),
    )


def _parse_location(data: dict[str, Any]) -> str | None:
    locations = data.get("locations")

    if not isinstance(locations, list):
        return None

    parsed_locations: list[str] = []

    for location in locations:
        if not isinstance(location, dict):
            continue

        parts = [
            str(location.get(field)).strip()
            for field in ("city", "state", "country")
            if location.get(field)
        ]

        value = ", ".join(part for part in parts if part)

        if value and value not in parsed_locations:
            parsed_locations.append(value)

    return ", ".join(parsed_locations) if parsed_locations else None


def _parse_text(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    return text or None


def _parse_skills(data: dict[str, Any]) -> list[str]:
    skills: list[str] = []

    for field in ("skills", "stack", "tools"):
        values = data.get(field)

        if not isinstance(values, list):
            continue

        for value in values:
            if isinstance(value, dict):
                name = value.get("name")
            else:
                name = value

            if name is None:
                continue

            cleaned = str(name).strip()

            if cleaned and cleaned not in skills:
                skills.append(cleaned)

    return skills


def _parse_timestamp(data: dict[str, Any]) -> datetime | None:
    value = data.get("posted_at")

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
