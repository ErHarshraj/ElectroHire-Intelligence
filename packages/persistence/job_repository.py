from abc import ABC, abstractmethod

from packages.domain.job import Job


class JobRepository(ABC):
    """Abstract persistence interface for canonical jobs."""

    @abstractmethod
    def save(self, job: Job) -> None:
        """Persist a job."""
        raise NotImplementedError

    @abstractmethod
    def get_by_source_job_id(
        self,
        source: str,
        source_job_id: str,
    ) -> Job | None:
        """Return a job by its source and source-specific identifier."""
        raise NotImplementedError

    @abstractmethod
    def list_jobs(self) -> list[Job]:
        """Return all persisted jobs."""
        raise NotImplementedError

    @abstractmethod
    def get_id_by_source_job_id(
        self,
        source: str,
        source_job_id: str,
    ) -> int | None:
        """Return the database ID for a source-specific job."""
        raise NotImplementedError
