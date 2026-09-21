from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

from pydantic import HttpUrl

from packages.domain.job import Job


def parse_job(data: dict[str, Any]) -> Job:
    """Convert a Hopin API record into the ElectroHire Job model."""

    job_id = str(data["id"])

    return Job(
        title=str(data["title"]),
        company=str(data.get("company") or "Unknown"),
        location=_parse_string(data.get("location")),
        description=_parse_string(data.get("description")),
        source="hopin",
        source_job_id=job_id,
        source_url=HttpUrl(_build_source_url(data)),
        employment_type=_parse_string(data.get("job_type")),
        experience_required=_parse_string(data.get("role_type")),
        skills=_parse_skills(data),
        posted_at=_parse_timestamp(data.get("posted_at")),
        discovered_at=datetime.now(timezone.utc),
        is_active=_parse_bool(data.get("is_active")),
    )


def _build_source_url(data: dict[str, Any]) -> str:
    job_id = str(data["id"])
    title = _parse_string(data.get("title")) or "job"

    slug = "-".join(title.lower().split())
    slug = quote(slug, safe="-")

    return f"https://hopinjobs.com/jobs/{slug}-{job_id}"


def _parse_string(value: Any) -> str | None:
    if value is None:
        return None

    cleaned = str(value).strip()
    return cleaned or None


def _parse_skills(data: dict[str, Any]) -> list[str]:
    values = [
        data.get("industry"),
        data.get("work_type"),
    ]

    return [
        value
        for value in (_parse_string(item) for item in values)
        if value is not None
    ]


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    return True


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
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)

        return parsed

    except ValueError:
        return None
