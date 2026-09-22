from __future__ import annotations

import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from pydantic import HttpUrl

from packages.domain.job import Job


def parse_job(data: dict[str, Any]) -> Job:
    """Convert a Startup Jobs RSS record into the ElectroHire Job model."""

    title, company = _parse_title(data["title"])
    description, location = _parse_description(data.get("description"))

    return Job(
        title=title,
        company=company,
        location=location,
        description=description,
        source="startup_jobs",
        source_job_id=_parse_source_job_id(data["guid"]),
        source_url=HttpUrl(data["guid"]),
        employment_type=None,
        experience_required=None,
        skills=[],
        posted_at=_parse_timestamp(data.get("pubDate")),
        discovered_at=datetime.now(timezone.utc),
    )


def _parse_title(value: Any) -> tuple[str, str]:
    """Extract job title and company from 'Job Title at Company'."""

    text = str(value).strip()

    if not text:
        raise ValueError("Startup Jobs title must not be empty.")

    match = re.match(r"^(.*)\s+at\s+(.+)$", text, re.IGNORECASE)

    if match:
        title = match.group(1).strip()
        company = match.group(2).strip()

        if title and company:
            return title, company

    return text, "Unknown"


def _parse_description(
    value: Any,
) -> tuple[str | None, str | None]:
    """Split the RSS description into description text and location."""

    if not value:
        return None, None

    lines = [
        line.strip()
        for line in str(value).splitlines()
        if line.strip()
    ]

    if not lines:
        return None, None

    if len(lines) == 1:
        return lines[0], None

    location = lines[-1]
    description = "\n".join(lines[:-1]).strip()

    return description or None, location or None


def _parse_source_job_id(value: Any) -> str:
    """Extract the numeric Startup Jobs listing ID from its GUID."""

    guid = str(value).strip()

    match = re.search(r"-(\d+)$", guid)

    if match:
        return match.group(1)

    return guid


def _parse_timestamp(value: Any) -> datetime | None:
    """Parse an RSS RFC 2822 publication timestamp."""

    if not value:
        return None

    try:
        parsed = parsedate_to_datetime(str(value))

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None
