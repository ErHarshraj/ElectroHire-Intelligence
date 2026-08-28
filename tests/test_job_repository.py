from datetime import datetime, timezone

from pydantic import HttpUrl

from packages.domain.job import Job
from packages.persistence.in_memory import InMemoryJobRepository


def make_job(source_job_id: str) -> Job:
    return Job(
        title="Embedded Hardware Engineer",
        company="Example Electronics",
        source="mock",
        source_job_id=source_job_id,
        source_url=HttpUrl(
            f"https://example.com/jobs/{source_job_id}"
        ),
        discovered_at=datetime.now(timezone.utc),
    )


def test_save_and_get_job() -> None:
    repository = InMemoryJobRepository()
    job = make_job("MOCK-001")

    repository.save(job)

    result = repository.get_by_source_job_id(
        "mock",
        "MOCK-001",
    )

    assert result == job


def test_get_unknown_job_returns_none() -> None:
    repository = InMemoryJobRepository()

    result = repository.get_by_source_job_id(
        "mock",
        "DOES-NOT-EXIST",
    )

    assert result is None


def test_list_jobs_returns_all_jobs() -> None:
    repository = InMemoryJobRepository()

    job_1 = make_job("MOCK-001")
    job_2 = make_job("MOCK-002")

    repository.save(job_1)
    repository.save(job_2)

    assert repository.list_jobs() == [job_1, job_2]
