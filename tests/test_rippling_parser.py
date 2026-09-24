from datetime import timezone

from packages.job_sources.rippling.parser import parse_rippling_job


def test_parse_rippling_job() -> None:
    job = parse_rippling_job(
        data={
            "jobPost": {
                "uuid": "89ca06b8-ebf8-4a40-91e3-ae09f818f66a",
                "name": "Staff Embedded Firmware Engineer",
                "companyName": "TYLsemi, Inc.",
                "description": {
                    "company": "<p>TYLsemi builds semiconductor products.</p>",
                    "role": ("<p>Develop embedded firmware using C and C++.</p>"),
                },
                "employmentType": {
                    "label": "SALARIED_FT",
                    "id": "Salaried, full-time",
                },
                "createdOn": "2026-09-15T08:25:53.137000-07:00",
                "url": (
                    "https://ats.rippling.com/tylsemi/jobs/89ca06b8-ebf8-4a40-91e3-ae09f818f66a"
                ),
                "workLocations": ["Bengaluru, India"],
            }
        },
        company_name="Fallback Company",
        source_name="rippling",
    )

    assert job.title == "Staff Embedded Firmware Engineer"
    assert job.company == "TYLsemi, Inc."
    assert job.location == "Bengaluru, India"

    assert job.description is not None
    assert "TYLsemi builds semiconductor products." in job.description
    assert "Develop embedded firmware using C and C++." in job.description

    assert job.source == "rippling"
    assert job.source_job_id == "89ca06b8-ebf8-4a40-91e3-ae09f818f66a"
    assert (
        str(job.source_url) == "https://ats.rippling.com/tylsemi/jobs/"
        "89ca06b8-ebf8-4a40-91e3-ae09f818f66a"
    )

    assert job.employment_type == "Salaried, full-time"
    assert job.experience_required is None
    assert job.skills == []

    assert job.posted_at is not None
    assert job.posted_at.tzinfo == timezone.utc


def test_parse_rippling_job_uses_configured_company_as_fallback() -> None:
    job = parse_rippling_job(
        data={
            "jobPost": {
                "uuid": "job-1",
                "name": "Hardware Engineer",
                "description": {},
                "url": "https://ats.rippling.com/example/jobs/job-1",
            }
        },
        company_name="Configured Company",
        source_name="rippling",
    )

    assert job.company == "Configured Company"


def test_parse_rippling_job_multiple_locations() -> None:
    job = parse_rippling_job(
        data={
            "jobPost": {
                "uuid": "job-2",
                "name": "Embedded Engineer",
                "url": "https://ats.rippling.com/example/jobs/job-2",
                "workLocations": [
                    "Bengaluru, India",
                    "Pune, India",
                    "Bengaluru, India",
                ],
            }
        },
        company_name="Example",
        source_name="rippling",
    )

    assert job.location == "Bengaluru, India, Pune, India"


def test_parse_rippling_job_handles_missing_optional_fields() -> None:
    job = parse_rippling_job(
        data={
            "jobPost": {
                "uuid": "job-3",
                "name": "Firmware Engineer",
                "url": "https://ats.rippling.com/example/jobs/job-3",
            }
        },
        company_name="Example",
        source_name="rippling",
    )

    assert job.location is None
    assert job.description is None
    assert job.employment_type is None
    assert job.posted_at is None


def test_parse_rippling_job_handles_plain_text_description() -> None:
    job = parse_rippling_job(
        data={
            "jobPost": {
                "uuid": "job-4",
                "name": "PCB Engineer",
                "url": "https://ats.rippling.com/example/jobs/job-4",
                "description": {
                    "company": "Company description",
                    "role": "Role description",
                },
            }
        },
        company_name="Example",
        source_name="rippling",
    )

    assert job.description == ("Company description\n\nRole description")
