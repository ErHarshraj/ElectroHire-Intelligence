from datetime import datetime, timezone

from pydantic import HttpUrl

from packages.domain.job import Job
from packages.domain.job_status import JobStatus


def test_job_status_defaults_to_discovered() -> None:
    job = Job(
        title="Hardware Design Engineer",
        company="Test Company",
        source="test",
        source_url=HttpUrl("https://example.com/job/1"),
        discovered_at=datetime.now(timezone.utc),
    )

    assert job.status == JobStatus.DISCOVERED


def test_job_status_can_be_updated() -> None:
    job = Job(
        title="Hardware Design Engineer",
        company="Test Company",
        source="test",
        source_url=HttpUrl("https://example.com/job/1"),
        discovered_at=datetime.now(timezone.utc),
    )

    job.status = JobStatus.EVALUATED

    assert job.status == JobStatus.EVALUATED
