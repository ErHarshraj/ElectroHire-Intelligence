from datetime import datetime, timezone

from packages.job_sources.hopin.parser import parse_job


def test_parse_job() -> None:
    job = parse_job(
        {
            "id": "job-123",
            "company": "Example Electronics",
            "title": "Embedded Engineer",
            "description": "Design embedded systems.",
            "location": "Bangalore, India",
            "work_type": "Hybrid",
            "industry": "Technology",
            "role_type": "Embedded Engineer",
            "job_type": "Full-time",
            "posted_at": "2026-08-21T03:52:44",
            "is_active": True,
        }
    )

    assert job.title == "Embedded Engineer"
    assert job.company == "Example Electronics"
    assert job.location == "Bangalore, India"
    assert job.description == "Design embedded systems."
    assert job.source == "hopin"
    assert job.source_job_id == "job-123"
    assert str(job.source_url) == (
        "https://hopinjobs.com/jobs/"
        "embedded-engineer-job-123"
    )
    assert job.employment_type == "Full-time"
    assert job.experience_required == "Embedded Engineer"
    assert job.skills == ["Technology", "Hybrid"]
    assert job.posted_at == datetime(
        2026,
        8,
        21,
        3,
        52,
        44,
        tzinfo=timezone.utc,
    )
    assert job.is_active is True


def test_parse_missing_optional_fields() -> None:
    job = parse_job(
        {
            "id": "job-456",
            "company": "Example",
            "title": "PCB Designer",
        }
    )

    assert job.location is None
    assert job.description is None
    assert job.employment_type is None
    assert job.experience_required is None
    assert job.skills == []
    assert job.posted_at is None
    assert job.is_active is True


def test_parse_inactive_job() -> None:
    job = parse_job(
        {
            "id": "job-789",
            "company": "Example",
            "title": "Hardware Engineer",
            "is_active": False,
        }
    )

    assert job.is_active is False


def test_parse_invalid_timestamp() -> None:
    job = parse_job(
        {
            "id": "job-999",
            "company": "Example",
            "title": "Electronics Engineer",
            "posted_at": "invalid-date",
        }
    )

    assert job.posted_at is None
