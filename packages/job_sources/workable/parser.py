from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import HttpUrl

from packages.domain.job import Job


def parse_workable_job(
    *,
    data: dict[str, Any],
    company_name: str,
    source_name: str,
) -> Job:
    """Convert a Workable job payload into the canonical Job model."""
    title = str(data.get("title") or "").strip()

    location = _parse_location(data)

    description = data.get("description")
    if description is not None:
        description = str(description)

    source_job_id = str(data.get("shortcode") or "").strip() or None

    source_url = str(data.get("url") or "").strip()

    employment_type = _parse_text(data.get("employment_type"))
    experience_required = _parse_text(data.get("experience"))

    posted_at = _parse_datetime(data.get("published_on"))

    return Job(
        title=title,
        company=company_name,
        location=location,
        description=description,
        source=source_name,
        source_job_id=source_job_id,
        source_url=HttpUrl(source_url),
        employment_type=employment_type,
        experience_required=experience_required,
        skills=[],
        posted_at=posted_at,
        discovered_at=datetime.now(timezone.utc),
    )


def _parse_location(data: dict[str, Any]) -> str | None:
    """Extract the best available Workable location."""
    locations = data.get("locations")

    if isinstance(locations, list):
        values: list[str] = []

        for location in locations:
            if isinstance(location, dict):
                value = location.get("location_str") or location.get("city")
            else:
                value = location

            if value:
                text = str(value).strip()
                if text and text not in values:
                    values.append(text)

        if values:
            return ", ".join(values)

    value = data.get("location")

    if isinstance(value, dict):
        parts = [
            str(value.get(key)).strip()
            for key in ("city", "state", "country")
            if value.get(key)
        ]
        return ", ".join(parts) or None

    return _parse_text(value)


def _parse_text(value: Any) -> str | None:
    """Convert an optional Workable text field to a clean string."""
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def _parse_datetime(value: Any) -> datetime | None:
    """Parse a Workable ISO-8601 timestamp."""
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)
