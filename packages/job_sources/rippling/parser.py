from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any

from pydantic import HttpUrl

from packages.domain.job import Job


class _HTMLTextParser(HTMLParser):
    """Convert simple HTML content into readable text."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()

        if text:
            self.parts.append(text)

    def get_text(self) -> str:
        return " ".join(self.parts)


def parse_rippling_job(
    *,
    data: dict[str, Any],
    company_name: str,
    source_name: str,
) -> Job:
    """Convert a Rippling apiData payload into the canonical Job model."""
    job_post = data.get("jobPost")

    if not isinstance(job_post, dict):
        raise ValueError("Rippling payload must contain a jobPost object.")

    title = str(job_post.get("name") or "").strip()

    if not title:
        raise ValueError("Rippling jobPost must contain a job name.")

    company = str(job_post.get("companyName") or company_name).strip() or company_name

    location = _parse_locations(job_post.get("workLocations"))

    description = _parse_description(job_post.get("description"))

    source_job_id = _parse_text(job_post.get("uuid"))

    source_url = _parse_text(job_post.get("url"))

    if not source_url:
        raise ValueError("Rippling jobPost must contain a job URL.")

    employment_type = _parse_employment_type(job_post.get("employmentType"))

    posted_at = _parse_datetime(job_post.get("createdOn"))

    return Job(
        title=title,
        company=company,
        location=location,
        description=description,
        source=source_name,
        source_job_id=source_job_id,
        source_url=HttpUrl(source_url),
        employment_type=employment_type,
        experience_required=None,
        skills=[],
        posted_at=posted_at,
        discovered_at=datetime.now(timezone.utc),
    )


def _parse_locations(value: Any) -> str | None:
    """Convert Rippling work locations into a readable string."""
    if not isinstance(value, list):
        return _parse_text(value)

    locations: list[str] = []

    for item in value:
        text = _parse_text(item)

        if text and text not in locations:
            locations.append(text)

    return ", ".join(locations) or None


def _parse_description(value: Any) -> str | None:
    """Convert Rippling company/role HTML descriptions to plain text."""
    if not isinstance(value, dict):
        return _parse_html(value)

    sections: list[str] = []

    for key in ("company", "role"):
        text = _parse_html(value.get(key))

        if text:
            sections.append(text)

    return "\n\n".join(sections) or None


def _parse_html(value: Any) -> str | None:
    """Convert HTML or plain text into normalized readable text."""
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    parser = _HTMLTextParser()
    parser.feed(text)

    parsed = parser.get_text()

    return parsed or None


def _parse_employment_type(value: Any) -> str | None:
    """Extract the human-readable Rippling employment type."""
    if isinstance(value, dict):
        return _parse_text(value.get("id") or value.get("label"))

    return _parse_text(value)


def _parse_text(value: Any) -> str | None:
    """Convert an optional value into a clean string."""
    if value is None:
        return None

    text = str(value).strip()

    return text or None


def _parse_datetime(value: Any) -> datetime | None:
    """Parse a Rippling ISO-8601 timestamp."""
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
