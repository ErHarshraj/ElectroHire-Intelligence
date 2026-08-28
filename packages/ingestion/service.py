from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.persistence.job_repository import JobRepository


class IngestionService:
    """Coordinates job discovery and persistence."""

    def __init__(
        self,
        source: JobSource,
        repository: JobRepository,
    ) -> None:
        self.source = source
        self.repository = repository

    def ingest(self) -> list[Job]:
        """Fetch jobs from the source and persist them."""

        jobs = list(self.source.fetch_jobs())

        for job in jobs:
            self.repository.save(job)

        return jobs
