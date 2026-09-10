from abc import ABC, abstractmethod
from datetime import datetime, timezone

from packages.scheduler.models import SchedulerRunResult


class ScheduledWork(ABC):
    """Defines one complete autonomous worker cycle."""

    @abstractmethod
    def run_cycle(self) -> None:
        raise NotImplementedError


class SchedulerService:
    """Executes a scheduled worker cycle."""

    def __init__(self, work: ScheduledWork) -> None:
        self.work = work

    def run_once(self) -> SchedulerRunResult:
        started_at = datetime.now(timezone.utc)

        try:
            self.work.run_cycle()
        except Exception as exc:
            completed_at = datetime.now(timezone.utc)

            return SchedulerRunResult(
                started_at=started_at,
                completed_at=completed_at,
                success=False,
                message=f"scheduled cycle failed: {exc}",
            )

        completed_at = datetime.now(timezone.utc)

        return SchedulerRunResult(
            started_at=started_at,
            completed_at=completed_at,
            success=True,
            message="scheduled cycle completed successfully",
        )
