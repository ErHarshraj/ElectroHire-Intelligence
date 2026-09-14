from collections.abc import Iterable
from typing import Any, cast

import pytest

from apps.worker.cycle import WorkerCycle
from packages.application.application_service import ApplicationService
from packages.application.approval import ApplicationApprovalService
from packages.application.discovery.target_discovery import ApplyTargetDiscovery
from packages.common.config import Settings
from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.observability.models import WorkerRunReport
from packages.persistence.application_repository import ApplicationRepository
from packages.persistence.decision_repository import DecisionRepository
from packages.persistence.job_repository import JobRepository


class FakeApplicationService:
    pass


class FakeApprovalService:
    pass


class FakeTargetDiscovery:
    pass


class FakeJobSource(JobSource):
    """Deterministic job source used by the worker report test."""

    def __init__(self, source_name: str) -> None:
        self._name = source_name

    @property
    def name(self) -> str:
        return self._name

    def fetch_jobs(self) -> Iterable[Job]:
        return []


def test_worker_cycle_returns_run_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        adzuna_app_id="test-app-id",
        adzuna_app_key="test-app-key",
        adzuna_queries=["hardware engineer", "embedded engineer"],
        adzuna_pages=1,
    )

    cycle = WorkerCycle(
        settings=settings,
        sources=[
            FakeJobSource("hardware"),
            FakeJobSource("embedded"),
        ],
        repository=cast(JobRepository, object()),
        decision_repository=cast(DecisionRepository, object()),
        application_repository=cast(ApplicationRepository, object()),
        application_service=cast(
            ApplicationService,
            FakeApplicationService(),
        ),
        target_discovery=cast(
            ApplyTargetDiscovery,
            FakeTargetDiscovery(),
        ),
        approval_service=cast(
            ApplicationApprovalService,
            FakeApprovalService(),
        ),
    )

    def fake_process_source(**kwargs: Any) -> tuple[int, int, int]:
        stats = kwargs["stats"]
        stats.apply_decisions = 2
        stats.targets_found = 1

        return 3, 2, 1

    monkeypatch.setattr(
        "apps.worker.cycle.process_source",
        fake_process_source,
    )

    monkeypatch.setattr(
        cycle,
        "run_approval_phase",
        lambda: None,
    )

    monkeypatch.setattr(
        "apps.worker.cycle.run_recovery_phase",
        lambda **kwargs: None,
    )

    report = cycle.run_cycle()

    assert isinstance(report, WorkerRunReport)
    assert report.success is True

    assert report.queries_processed == 2
    assert report.new_jobs == 6
    assert report.evaluated_jobs == 4
    assert report.ignored_jobs == 2

    assert report.application_stats.apply_decisions == 4
    assert report.application_stats.targets_found == 2

    assert report.completed_at >= report.started_at
    assert report.duration_seconds >= 0
