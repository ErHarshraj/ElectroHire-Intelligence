from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import HttpUrl

from packages.domain.job import Job


def parse_workday_job(
    *,
    summary: dict[str, Any],
    detail: dict[str, Any],
    company_name: str,
    source_name: str,
    external_url: str,
) -> Job:
    """Convert a Workday summary/detail pair into the canonical Job model."""
    title = str(
        detail.get("title")
        or summary.get("title")
        or ""
    ).strip()

    location = str(
        detail.get("location")
        or summary.get("locationsText")
        or ""
    ).strip() or None

    description = detail.get("jobDescription")

    if description is not None:
        description = str(description)

    source_job_id = str(
        detail.get("jobReqId")
        or detail.get("id")
        or summary.get("externalPath")
        or ""
    ).strip()

    employment_type = _parse_employment_type(detail)
    experience_required = _parse_experience(detail)

    return Job(
        title=title,
        company=company_name,
        location=location,
        description=description,
        source=source_name,
        source_job_id=source_job_id or None,
        source_url=HttpUrl(external_url),
        employment_type=employment_type,
        experience_required=experience_required,
        skills=_parse_skills(detail),
        posted_at=None,
        discovered_at=datetime.now(timezone.utc),
    )


def _parse_employment_type(data: dict[str, Any]) -> str | None:
    """Extract Workday's time type when the board provides one."""
    value = data.get("timeType")

    if not value:
        return None

    return str(value).strip() or None


def _parse_experience(data: dict[str, Any]) -> str | None:
    """Extract a Workday experience field when explicitly provided."""
    value = data.get("experience")

    if not value:
        return None

    return str(value).strip() or None


def _parse_skills(data: dict[str, Any]) -> list[str]:
    """Extract explicitly structured Workday skill values when available."""
    value = data.get("skills")

    if not isinstance(value, list):
        return []

    return [
        str(item).strip()
        for item in value
        if str(item).strip()
    ]
