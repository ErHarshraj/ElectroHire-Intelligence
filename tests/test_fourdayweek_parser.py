from datetime import datetime, timezone

from packages.job_sources.fourdayweek.parser import parse_job


def test_parse_job() -> None:
    job = parse_job(
        {
            "id": "job-123",
            "title": "Embedded Systems Engineer",
            "url": "https://4dayweek.io/job/embedded-systems-engineer-job-123",
            "description": "Design embedded systems.",
            "contract_type": "Full-time",
            "level": "Mid-level",
            "posted_at": "2026-08-21T03:52:44Z",
            "company": {
                "name": "Example Electronics",
            },
            "locations": [
                {
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "country": "India",
                },
            ],
            "skills": [
                {"name": "C"},
                {"name": "Embedded Systems"},
            ],
            "stack": [
                {"name": "STM32"},
                {"name": "C"},
            ],
            "tools": [
                {"name": "Git"},
            ],
        }
    )

    assert job.title == "Embedded Systems Engineer"
    assert job.company == "Example Electronics"
    assert job.location == "Bengaluru, Karnataka, India"
    assert job.description == "Design embedded systems."
    assert job.source == "fourdayweek"
    assert job.source_job_id == "job-123"
    assert str(job.source_url) == (
        "https://4dayweek.io/job/"
        "embedded-systems-engineer-job-123"
    )
    assert job.employment_type == "Full-time"
    assert job.experience_required == "Mid-level"
    assert job.skills == [
        "C",
        "Embedded Systems",
        "STM32",
        "Git",
    ]
    assert job.posted_at == datetime(
        2026,
        8,
        21,
        3,
        52,
        44,
        tzinfo=timezone.utc,
    )
    assert job.discovered_at.tzinfo is not None
    assert job.is_active is True


def test_parse_multiple_locations_without_duplicates() -> None:
    job = parse_job(
        {
            "id": "job-456",
            "title": "Hardware Engineer",
            "url": "https://4dayweek.io/job/hardware-engineer",
            "locations": [
                {
                    "city": "Bengaluru",
                    "country": "India",
                },
                {
                    "city": "Pune",
                    "state": "Maharashtra",
                    "country": "India",
                },
                {
                    "city": "Bengaluru",
                    "country": "India",
                },
            ],
        }
    )

    assert job.location == (
        "Bengaluru, India, Pune, Maharashtra, India"
    )


def test_parse_missing_optional_fields() -> None:
    job = parse_job(
        {
            "id": "job-789",
            "title": "PCB Designer",
            "url": "https://4dayweek.io/job/pcb-designer",
        }
    )

    assert job.company == "Unknown"
    assert job.location is None
    assert job.description is None
    assert job.employment_type is None
    assert job.experience_required is None
    assert job.skills == []
    assert job.posted_at is None
    assert job.is_active is True


def test_parse_invalid_timestamp() -> None:
    job = parse_job(
        {
            "id": "job-999",
            "title": "Electronics Engineer",
            "url": "https://4dayweek.io/job/electronics-engineer",
            "posted_at": "invalid-date",
        }
    )

    assert job.posted_at is None


def test_parse_naive_timestamp_as_utc() -> None:
    job = parse_job(
        {
            "id": "job-1000",
            "title": "Firmware Engineer",
            "url": "https://4dayweek.io/job/firmware-engineer",
            "posted_at": "2026-08-27T10:30:00",
        }
    )

    assert job.posted_at == datetime(
        2026,
        8,
        27,
        10,
        30,
        tzinfo=timezone.utc,
    )


def test_parse_skills_from_string_and_object_values() -> None:
    job = parse_job(
        {
            "id": "job-1001",
            "title": "Electronics Engineer",
            "url": "https://4dayweek.io/job/electronics-engineer",
            "skills": [
                {"name": "Python"},
                "C++",
            ],
            "stack": [
                {"name": "Python"},
                {"name": "KiCad"},
            ],
            "tools": [
                {"name": "KiCad"},
                "Git",
            ],
        }
    )

    assert job.skills == [
        "Python",
        "C++",
        "KiCad",
        "Git",
    ]
