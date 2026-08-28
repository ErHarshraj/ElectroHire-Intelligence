from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.persistence.job_repository import JobRepository


class IngestionService:
    """Coordinates job discovery, deduplication, and persistence."""

    def __init__(
        self,
        source: JobSource,
        repository: JobRepository,
    ) -> None:
        self.source = source
        self.repository = repository

    def ingest(self) -> list[Job]:
        """Fetch, deduplicate, and persist jobs from the source."""

        jobs = list(self.source.fetch_jobs())
        new_jobs: list[Job] = []

        for job in jobs:
            if job.source_job_id is not None:
                existing_job = self.repository.get_by_source_job_id(
                    job.source,
                    job.source_job_id,
                )

                if existing_job is not None:
                    continue

            self.repository.save(job)
            new_jobs.append(job)

        return new_jobs
