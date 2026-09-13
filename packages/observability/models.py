from dataclasses import dataclass
from datetime import datetime

from packages.application.stats import ApplicationRunStats


@dataclass(frozen=True)
class WorkerRunReport:
    started_at: datetime
    completed_at: datetime
    success: bool

    queries_processed: int
    new_jobs: int
    evaluated_jobs: int
    ignored_jobs: int

    application_stats: ApplicationRunStats

    error: str | None = None

    @property
    def duration_seconds(self) -> float:
        return (
            self.completed_at - self.started_at
        ).total_seconds()
