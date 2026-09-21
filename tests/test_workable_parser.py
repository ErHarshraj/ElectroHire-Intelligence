from __future__ import annotations

from datetime import datetime, timezone

from packages.job_sources.workable.parser import parse_workable_job


def test_parse_workable_job() -> None:
    data = {
        "title": "Embedded Systems Engineer",
        "shortcode": "ABC123",
        "url": "https://apply.workable.com/j/ABC123",
        "description": "<p>Embedded systems role.</p>",
        "employment_type": "Full-time",
        "experience": "1-3 years",
        "published_on": "2026-08-27T10:30:00Z",
        "location": "Dublin, Ireland",
    }

    job = parse_workable_job(
        data=data,
        company_name="Example Electronics",
        source_name="workable",
    )

    assert job.title == "Embedded Systems Engineer"
    assert job.company == "Example Electronics"
    assert job.location == "Dublin, Ireland"
    assert job.description == "<p>Embedded systems role.</p>"
    assert job.source == "workable"
    assert job.source_job_id == "ABC123"
    assert str(job.source_url) == "https://apply.workable.com/j/ABC123"
    assert job.employment_type == "Full-time"
    assert job.experience_required == "1-3 years"
    assert job.skills == []
    assert job.posted_at == datetime(
        2026,
        8,
        27,
        10,
        30,
        tzinfo=timezone.utc,
    )
    assert job.discovered_at.tzinfo is not None


def test_parse_workable_job_multiple_locations() -> None:
    data = {
        "title": "Hardware Engineer",
        "shortcode": "HW123",
        "url": "https://apply.workable.com/j/HW123",
        "locations": [
            {"location_str": "Bengaluru, India"},
            {"location_str": "Pune, India"},
            {"location_str": "Bengaluru, India"},
        ],
    }

    job = parse_workable_job(
        data=data,
        company_name="Example Electronics",
        source_name="workable",
    )

    assert job.location == "Bengaluru, India, Pune, India"


def test_parse_workable_job_location_object() -> None:
    data = {
        "title": "PCB Design Engineer",
        "shortcode": "PCB123",
        "url": "https://apply.workable.com/j/PCB123",
        "location": {
            "city": "Pune",
            "state": "Maharashtra",
            "country": "India",
        },
    }

    job = parse_workable_job(
        data=data,
        company_name="Example Electronics",
        source_name="workable",
    )

    assert job.location == "Pune, Maharashtra, India"


def test_parse_workable_job_handles_missing_optional_fields() -> None:
    data = {
        "title": "Electronics Engineer",
        "shortcode": "ELEC123",
        "url": "https://apply.workable.com/j/ELEC123",
    }

    job = parse_workable_job(
        data=data,
        company_name="Example Electronics",
        source_name="workable",
    )

    assert job.location is None
    assert job.description is None
    assert job.employment_type is None
    assert job.experience_required is None
    assert job.posted_at is None
    assert job.skills == []


def test_parse_workable_job_invalid_posted_at_becomes_none() -> None:
    data = {
        "title": "Firmware Engineer",
        "shortcode": "FW123",
        "url": "https://apply.workable.com/j/FW123",
        "published_on": "not-a-date",
    }

    job = parse_workable_job(
        data=data,
        company_name="Example Electronics",
        source_name="workable",
    )

    assert job.posted_at is None


def test_parse_workable_job_normalizes_naive_timestamp() -> None:
    data = {
        "title": "Firmware Engineer",
        "shortcode": "FW456",
        "url": "https://apply.workable.com/j/FW456",
        "published_on": "2026-08-27T10:30:00",
    }

    job = parse_workable_job(
        data=data,
        company_name="Example Electronics",
        source_name="workable",
    )

    assert job.posted_at == datetime(
        2026,
        8,
        27,
        10,
        30,
        tzinfo=timezone.utc,
    )
