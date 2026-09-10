from datetime import datetime

import pytest

from packages.scheduler.models import SchedulerConfig
from packages.scheduler.service import ScheduledWork, SchedulerService


class FakeWork(ScheduledWork):
    def __init__(self, failures: int = 0) -> None:
        self.calls = 0
        self.failures = failures

    def run_cycle(self) -> None:
        self.calls += 1

        if self.calls <= self.failures:
            raise RuntimeError("test failure")


def test_scheduler_runs_one_cycle() -> None:
    work = FakeWork()
    scheduler = SchedulerService(work)

    result = scheduler.run_once()

    assert work.calls == 1
    assert result.success is True
    assert isinstance(result.started_at, datetime)
    assert isinstance(result.completed_at, datetime)


def test_scheduler_reports_cycle_failure() -> None:
    work = FakeWork(failures=1)
    scheduler = SchedulerService(work)

    result = scheduler.run_once()

    assert work.calls == 1
    assert result.success is False
    assert "test failure" in result.message


def test_scheduler_has_safe_defaults() -> None:
    config = SchedulerConfig()

    assert config.discovery_interval_minutes == 60
    assert config.recovery_interval_minutes == 30


def test_scheduler_rejects_invalid_intervals() -> None:
    with pytest.raises(ValueError):
        SchedulerConfig(discovery_interval_minutes=0)

    with pytest.raises(ValueError):
        SchedulerConfig(recovery_interval_minutes=-1)


def test_scheduler_runs_periodically() -> None:
    work = FakeWork()

    sleep_calls: list[float] = []

    scheduler: SchedulerService

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

        if len(sleep_calls) >= 3:
            scheduler.stop()

    scheduler = SchedulerService(
        work=work,
        config=SchedulerConfig(discovery_interval_minutes=5),
        sleep_func=fake_sleep,
    )

    scheduler.run_forever()

    assert work.calls == 3
    assert sleep_calls == [300, 300, 300]


def test_scheduler_can_stop_without_running_cycle() -> None:
    work = FakeWork()
    scheduler = SchedulerService(work)

    scheduler.stop()

    assert scheduler.is_running is False


def test_scheduler_rejects_zero_runtime_interval() -> None:
    work = FakeWork()
    scheduler = SchedulerService(work)

    with pytest.raises(ValueError):
        scheduler.run_forever(interval_minutes=0)


def test_scheduler_settings_expose_intervals() -> None:
    from packages.common.config import Settings

    settings = Settings(
        scheduler_discovery_interval_minutes=90,
        scheduler_recovery_interval_minutes=45,
    )

    config = SchedulerConfig(
        discovery_interval_minutes=settings.scheduler_discovery_interval_minutes,
        recovery_interval_minutes=settings.scheduler_recovery_interval_minutes,
    )

    assert config.discovery_interval_minutes == 90
    assert config.recovery_interval_minutes == 45


def test_scheduler_continues_after_failed_cycle() -> None:
    work = FakeWork(failures=1)

    sleep_calls: list[float] = []

    scheduler: SchedulerService

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

        if len(sleep_calls) >= 2:
            scheduler.stop()

    scheduler = SchedulerService(
        work=work,
        config=SchedulerConfig(discovery_interval_minutes=1),
        sleep_func=fake_sleep,
    )

    scheduler.run_forever()

    assert work.calls == 2
    assert sleep_calls == [60, 60]
