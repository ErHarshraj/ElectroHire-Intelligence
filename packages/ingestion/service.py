from packages.domain.job import Job
from packages.job_sources.base import JobSource


class IngestionService:
    """Coordinates job discovery from a job source."""

    def __init__(self, source: JobSource) -> None:
        self.source = source

    def ingest(self) -> list[Job]:
        """Fetch and return canonical jobs from the configured source."""
        return list(self.source.fetch_jobs())
