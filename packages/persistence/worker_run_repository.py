from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from packages.application.stats import ApplicationRunStats


@dataclass(frozen=True)
class WorkerRunRecord:
    """Complete persisted worker run report."""

    started_at: datetime
    completed_at: datetime
    success: bool

    queries_processed: int
    new_jobs: int
    evaluated_jobs: int
    ignored_jobs: int

    application_stats: ApplicationRunStats

    error: str | None = None
    id: int | None = None


class WorkerRunRepository(ABC):
    """Persistence interface for worker run reports."""

    @abstractmethod
    def save(self, record: WorkerRunRecord) -> int:
        """Persist a worker run and return its generated ID."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(
        self,
        worker_run_id: int,
    ) -> WorkerRunRecord | None:
        """Return a worker run by ID."""
        raise NotImplementedError

    @abstractmethod
    def list_recent(
        self,
        limit: int = 20,
    ) -> list[WorkerRunRecord]:
        """Return the most recent worker runs."""
        raise NotImplementedError
