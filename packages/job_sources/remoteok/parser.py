from datetime import datetime, timezone
from typing import Any

from pydantic import HttpUrl

from packages.domain.job import Job


def parse_job(data: dict[str, Any]) -> Job:
    """Convert one Remote OK job record into the internal Job model."""

    return Job(
        title=str(data["position"]),
        company=str(data.get("company") or "Unknown"),
        location=_parse_location(data),
        description=data.get("description"),
        source="remoteok",
        source_job_id=str(data["id"]),
        source_url=HttpUrl(
            data.get("url")
            or data.get("apply_url")
            or f"https://remoteok.com/remote-jobs/{data['id']}"
        ),
        employment_type=_parse_employment_type(data),
        experience_required=None,
        skills=_parse_tags(data),
        posted_at=_parse_timestamp(data),
        discovered_at=datetime.now(timezone.utc),
    )


def _parse_location(data: dict[str, Any]) -> str | None:
    """Return the Remote OK location when available."""

    location = data.get("location")

    if location:
        return str(location)

    return None


def _parse_employment_type(data: dict[str, Any]) -> str | None:
    """Extract employment type when Remote OK provides one."""

    employment_type = data.get("employment_type")

    if employment_type:
        return str(employment_type)

    return None


def _parse_tags(data: dict[str, Any]) -> list[str]:
    """Convert Remote OK tags into a normalized string list."""

    tags = data.get("tags")

    if not isinstance(tags, list):
        return []

    return [
        str(tag).strip()
        for tag in tags
        if str(tag).strip()
    ]


def _parse_timestamp(data: dict[str, Any]) -> datetime | None:
    """Convert Remote OK publication timestamp into UTC."""

    epoch = data.get("epoch")

    if epoch is not None:
        return datetime.fromtimestamp(
            float(epoch),
            tz=timezone.utc,
        )

    value = data.get("date")

    if not value:
        return None

    try:
        return datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except ValueError:
        return None
