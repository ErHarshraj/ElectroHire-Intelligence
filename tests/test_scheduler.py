from packages.scheduler.models import SchedulerConfig
from packages.scheduler.service import ScheduledWork, SchedulerService


class RecordingWork(ScheduledWork):
    def __init__(self) -> None:
        self.calls = 0

    def run_cycle(self) -> None:
        self.calls += 1


class FailingWork(ScheduledWork):
    def run_cycle(self) -> None:
        raise RuntimeError("test failure")


def test_scheduler_runs_one_cycle() -> None:
    work = RecordingWork()
    scheduler = SchedulerService(work)

    result = scheduler.run_once()

    assert result.success is True
    assert result.message == "scheduled cycle completed successfully"
    assert work.calls == 1
    assert result.completed_at >= result.started_at


def test_scheduler_does_not_hide_cycle_failure() -> None:
    scheduler = SchedulerService(FailingWork())

    result = scheduler.run_once()

    assert result.success is False
    assert "scheduled cycle failed" in result.message
    assert "test failure" in result.message
    assert result.completed_at >= result.started_at


def test_scheduler_config_has_safe_defaults() -> None:
    config = SchedulerConfig()

    assert config.discovery_interval_minutes == 60
    assert config.recovery_interval_minutes == 30


def test_scheduler_can_run_multiple_cycles() -> None:
    work = RecordingWork()
    scheduler = SchedulerService(work)

    first = scheduler.run_once()
    second = scheduler.run_once()

    assert first.success is True
    assert second.success is True
    assert work.calls == 2
