from datetime import datetime, timezone

from packages.job_sources.ayla.parser import parse_job


def test_parse_job() -> None:
    job = parse_job(
        {
            "id": "ayla-job-123",
            "title": "Senior Hardware Engineer",
            "agency": "Example Defense Systems",
            "organizationName": "Example Defense Systems",
            "primaryLocationText": "Boston, MA",
            "description": "Design advanced electronic hardware.",
            "sourceUrl": (
                "https://example.com/careers/"
                "senior-hardware-engineer"
            ),
            "applicationUrl": (
                "https://example.com/apply/"
                "senior-hardware-engineer"
            ),
            "employmentType": "full-time",
            "seniorityLevel": "senior",
            "skills": [
                "Circuit Design",
                "PCB Design",
            ],
            "mustHaveSkills": [
                "Embedded Systems",
                "PCB Design",
            ],
            "preferredSkills": [
                "FPGA",
            ],
            "postedDate": "2026-09-20T10:30:00Z",
        }
    )

    assert job.title == "Senior Hardware Engineer"
    assert job.company == "Example Defense Systems"
    assert job.location == "Boston, MA"
    assert job.description == (
        "Design advanced electronic hardware."
    )
    assert job.source == "ayla"
    assert job.source_job_id == "ayla-job-123"
    assert str(job.source_url) == (
        "https://example.com/careers/"
        "senior-hardware-engineer"
    )
    assert job.employment_type == "full-time"
    assert job.experience_required == "senior"
    assert job.skills == [
        "Circuit Design",
        "PCB Design",
        "Embedded Systems",
        "FPGA",
    ]
    assert job.posted_at == datetime(
        2026,
        9,
        20,
        10,
        30,
        tzinfo=timezone.utc,
    )
    assert job.discovered_at.tzinfo is not None
    assert job.is_active is True


def test_parse_location_fallback() -> None:
    job = parse_job(
        {
            "id": "ayla-job-124",
            "title": "FPGA Engineer",
            "sourceUrl": "https://example.com/jobs/fpga-engineer",
            "city": "Austin",
            "state": "Texas",
            "countryCode": "US",
        }
    )

    assert job.location == "Austin, Texas, US"


def test_parse_organization_name_fallback() -> None:
    job = parse_job(
        {
            "id": "ayla-job-125",
            "title": "Embedded Engineer",
            "organizationName": "Example Robotics",
            "sourceUrl": "https://example.com/jobs/embedded",
        }
    )

    assert job.company == "Example Robotics"


def test_parse_missing_optional_fields() -> None:
    job = parse_job(
        {
            "id": "ayla-job-126",
            "title": "PCB Designer",
            "sourceUrl": "https://example.com/jobs/pcb-designer",
        }
    )

    assert job.company == "Unknown"
    assert job.location is None
    assert job.description is None
    assert job.employment_type is None
    assert job.experience_required is None
    assert job.skills == []
    assert job.posted_at is None


def test_parse_raw_description_fallback() -> None:
    job = parse_job(
        {
            "id": "ayla-job-127",
            "title": "Electronics Engineer",
            "sourceUrl": "https://example.com/jobs/electronics",
            "rawJobDescription": "Raw job description.",
        }
    )

    assert job.description == "Raw job description."


def test_parse_experience_dict() -> None:
    job = parse_job(
        {
            "id": "ayla-job-128",
            "title": "Hardware Engineer",
            "sourceUrl": "https://example.com/jobs/hardware",
            "experience": {
                "min": 3,
                "max": 7,
            },
        }
    )

    assert job.experience_required == "3-7"


def test_parse_invalid_timestamp() -> None:
    job = parse_job(
        {
            "id": "ayla-job-129",
            "title": "Firmware Engineer",
            "sourceUrl": "https://example.com/jobs/firmware",
            "postedDate": "invalid-date",
        }
    )

    assert job.posted_at is None


def test_parse_naive_timestamp_as_utc() -> None:
    job = parse_job(
        {
            "id": "ayla-job-130",
            "title": "Embedded Engineer",
            "sourceUrl": "https://example.com/jobs/embedded",
            "postedDate": "2026-09-21T10:30:00",
        }
    )

    assert job.posted_at == datetime(
        2026,
        9,
        21,
        10,
        30,
        tzinfo=timezone.utc,
    )
