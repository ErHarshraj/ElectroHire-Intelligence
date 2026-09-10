from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime, timezone
from time import sleep

from packages.scheduler.models import SchedulerConfig, SchedulerRunResult


class ScheduledWork(ABC):
    """Defines one complete autonomous worker cycle."""

    @abstractmethod
    def run_cycle(self) -> None:
        raise NotImplementedError


class SchedulerService:
    """Runs worker cycles periodically without external dependencies."""

    def __init__(
        self,
        work: ScheduledWork,
        config: SchedulerConfig | None = None,
        sleep_func: Callable[[float], None] = sleep,
    ) -> None:
        self.work = work
        self.config = config or SchedulerConfig()
        self.sleep_func = sleep_func
        self._running = False

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

    def run_forever(
        self,
        interval_minutes: int | None = None,
    ) -> None:
        """Run worker cycles until stop() is requested."""

        interval = (
            interval_minutes
            if interval_minutes is not None
            else self.config.discovery_interval_minutes
        )

        if interval <= 0:
            raise ValueError("scheduler interval must be greater than zero")

        if self._running:
            raise RuntimeError("scheduler is already running")

        self._running = True

        try:
            while self._running:
                result = self.run_once()
                print(result.message)

                if not self._running:
                    break

                self.sleep_func(interval * 60)
        finally:
            self._running = False

    def stop(self) -> None:
        """Request graceful scheduler shutdown."""

        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running
