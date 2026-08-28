from pydantic import HttpUrl

from packages.domain.job import Job
from packages.persistence.job_repository import JobRepository


class MemoryJobRepository(JobRepository):
    def __init__(self) -> None:
        self.jobs: list[Job] = []

    def save(self, job: Job) -> None:
        self.jobs.append(job)

    def get_by_source_job_id(
        self,
        source: str,
        source_job_id: str,
    ) -> Job | None:
        for job in self.jobs:
            if (
                job.source == source
                and job.source_job_id == source_job_id
            ):
                return job

        return None

    def list_jobs(self) -> list[Job]:
        return list(self.jobs)


def test_repository_contract() -> None:
    repository = MemoryJobRepository()

    job = Job(
        title="Embedded Hardware Engineer",
        company="Example Electronics",
        source="mock",
        source_job_id="MOCK-001",
        source_url=HttpUrl("https://example.com/jobs/MOCK-001"),
        discovered_at=__import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
    )

    repository.save(job)

    assert repository.get_by_source_job_id(
        "mock",
        "MOCK-001",
    ) == job

    assert repository.get_by_source_job_id(
        "mock",
        "DOES-NOT-EXIST",
    ) is None

    assert repository.list_jobs() == [job]
