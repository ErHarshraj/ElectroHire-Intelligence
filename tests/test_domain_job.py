from datetime import datetime, timezone

from pydantic import HttpUrl

from packages.domain.job import Job


def test_job_creation() -> None:
    job = Job(
        title="Embedded Hardware Engineer",
        company="Example Electronics",
        location="Bengaluru, India",
        description="Design embedded hardware and PCB systems.",
        source="example_source",
        source_job_id="JOB-001",
        source_url=HttpUrl("https://example.com/jobs/JOB-001"),
        employment_type="Full-time",
        experience_required="0-2 years",
        skills=["Embedded C", "PCB Design", "STM32"],
        posted_at=datetime(2026, 8, 28, tzinfo=timezone.utc),
        discovered_at=datetime(2026, 8, 28, tzinfo=timezone.utc),
    )

    assert job.title == "Embedded Hardware Engineer"
    assert job.company == "Example Electronics"
    assert job.source_job_id == "JOB-001"
    assert "STM32" in job.skills
    assert job.is_active is True
