from packages.domain.job import Job
from packages.persistence.job_repository import JobRepository


class InMemoryJobRepository(JobRepository):
    """In-memory implementation of the job repository."""

    def __init__(self) -> None:
        self._jobs: list[Job] = []

    def save(self, job: Job) -> None:
        """Store a job in memory."""
        self._jobs.append(job)

    def get_by_source_job_id(
        self,
        source: str,
        source_job_id: str,
    ) -> Job | None:
        """Find a job by source and source-specific ID."""
        for job in self._jobs:
            if (
                job.source == source
                and job.source_job_id == source_job_id
            ):
                return job

        return None

    def list_jobs(self) -> list[Job]:
        """Return all stored jobs."""
        return list(self._jobs)
