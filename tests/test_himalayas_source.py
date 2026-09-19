from datetime import datetime, timezone
from typing import Any

import pytest

from packages.job_sources.himalayas.client import HimalayasClient
from packages.job_sources.himalayas.parser import parse_job
from packages.job_sources.himalayas.source import HimalayasJobSource


def sample_job() -> dict[str, Any]:
    return {
        "title": "Embedded Hardware Engineer",
        "companyName": "Example Robotics",
        "companySlug": "example-robotics",
        "employmentType": "Full Time",
        "seniority": ["Mid"],
        "locationRestrictions": ["India"],
        "description": "<p>Design embedded hardware.</p>",
        "pubDate": 1789811612,
        "applicationLink": (
            "https://himalayas.app/companies/example-robotics/"
            "jobs/embedded-hardware-engineer"
        ),
        "guid": (
            "https://himalayas.app/companies/example-robotics/"
            "jobs/embedded-hardware-engineer"
        ),
    }


def test_parse_job_maps_himalayas_fields() -> None:
    job = parse_job(sample_job())

    assert job.title == "Embedded Hardware Engineer"
    assert job.company == "Example Robotics"
    assert job.location == "India"
    assert job.description == "<p>Design embedded hardware.</p>"
    assert job.source == "himalayas"
    assert job.source_job_id.startswith("https://himalayas.app/")
    assert str(job.source_url).startswith("https://himalayas.app/")
    assert job.employment_type == "Full Time"
    assert job.experience_required == "Mid"
    assert job.posted_at == datetime.fromtimestamp(
        1789811612,
        tz=timezone.utc,
    )
    assert job.discovered_at.tzinfo == timezone.utc


def test_parse_job_uses_location_when_restrictions_are_empty() -> None:
    data = sample_job()
    data["locationRestrictions"] = []
    data["location"] = "Remote"

    job = parse_job(data)

    assert job.location == "Remote"


def test_parse_job_handles_missing_optional_fields() -> None:
    data = sample_job()
    data.pop("employmentType")
    data.pop("seniority")
    data.pop("locationRestrictions")
    data.pop("description")

    job = parse_job(data)

    assert job.employment_type is None
    assert job.experience_required is None
    assert job.location is None
    assert job.description is None


def test_himalayas_source_uses_cursor_pagination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = [
        {
            "jobs": [sample_job()],
            "nextCursor": "cursor-1",
        },
        {
            "jobs": [
                {
                    **sample_job(),
                    "guid": "job-2",
                    "title": "Firmware Engineer",
                }
            ],
            "nextCursor": None,
        },
    ]

    calls: list[str | None] = []

    def fake_search_jobs(
        self: HimalayasClient,
        *,
        limit: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        calls.append(cursor)
        return responses[len(calls) - 1]

    monkeypatch.setattr(
        HimalayasClient,
        "search_jobs",
        fake_search_jobs,
    )

    source = HimalayasJobSource(
        client=HimalayasClient(),
        limit=50,
    )

    jobs = list(source.fetch_jobs())

    assert len(jobs) == 2
    assert jobs[0].title == "Embedded Hardware Engineer"
    assert jobs[1].title == "Firmware Engineer"
    assert calls == [None, "cursor-1"]


def test_himalayas_source_rejects_invalid_jobs_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_search_jobs(
        self: HimalayasClient,
        *,
        limit: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        return {
            "jobs": "invalid",
            "nextCursor": None,
        }

    monkeypatch.setattr(
        HimalayasClient,
        "search_jobs",
        fake_search_jobs,
    )

    source = HimalayasJobSource(client=HimalayasClient())

    with pytest.raises(
        TypeError,
        match="jobs field must be a list",
    ):
        list(source.fetch_jobs())
