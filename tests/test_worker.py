import pytest

from apps.worker.main import process_source, run
from packages.common.config import get_settings
from packages.job_sources.mock import MockJobSource
from packages.persistence.in_memory import InMemoryJobRepository
from packages.persistence.in_memory_decision import InMemoryDecisionRepository


def test_worker_requires_at_least_one_job_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_settings.cache_clear()

    monkeypatch.setenv("ADZUNA_APP_ID", "")
    monkeypatch.setenv("ADZUNA_APP_KEY", "")
    monkeypatch.setenv("GREENHOUSE_BOARDS", "[]")
    monkeypatch.setenv("LEVER_BOARDS", "[]")

    with pytest.raises(
        RuntimeError,
        match="No job sources are configured",
    ):
        run()

    get_settings.cache_clear()


def test_worker_does_not_require_adzuna_when_other_source_is_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_settings.cache_clear()

    monkeypatch.setenv("ADZUNA_APP_ID", "")
    monkeypatch.setenv("ADZUNA_APP_KEY", "")
    monkeypatch.setenv(
        "LEVER_BOARDS",
        '["Example Electronics:example-electronics"]',
    )

    class FakeCycle:
        def run_cycle(self):
            from datetime import datetime, timezone

            from packages.application.stats import ApplicationRunStats
            from packages.observability.models import WorkerRunReport

            now = datetime.now(timezone.utc)

            return WorkerRunReport(
                started_at=now,
                completed_at=now,
                success=True,
                queries_processed=1,
                new_jobs=0,
                evaluated_jobs=0,
                ignored_jobs=0,
                application_stats=ApplicationRunStats(),
            )

    monkeypatch.setattr(
        "apps.worker.main.build_worker_cycle",
        lambda settings, session: FakeCycle(),
    )

    run()

    get_settings.cache_clear()


def test_process_source_evaluates_new_jobs() -> None:
    source = MockJobSource()
    repository = InMemoryJobRepository()
    decision_repository = InMemoryDecisionRepository()

    new_count, evaluated_count, ignored_count = process_source(
        source=source,
        repository=repository,
        decision_repository=decision_repository,
    )

    assert new_count == 2
    assert evaluated_count == 2
    assert ignored_count == 0

    assert len(decision_repository.decisions) == 2


def test_process_source_persists_decisions() -> None:
    source = MockJobSource()
    repository = InMemoryJobRepository()
    decision_repository = InMemoryDecisionRepository()

    process_source(
        source=source,
        repository=repository,
        decision_repository=decision_repository,
    )

    decisions = decision_repository.decisions

    assert len(decisions) == 2

    for decision in decisions:
        assert decision.action.value in {"apply", "alert", "ignore"}
        assert 0.0 <= decision.relevance_score <= 100.0
        assert 0.0 <= decision.ranking_score <= 100.0
        assert decision.priority in {
            "HIGH",
            "MEDIUM",
            "LOW",
            "VERY_LOW",
        }
        assert decision.reasons


def test_process_source_does_not_reprocess_duplicates() -> None:
    source = MockJobSource()
    repository = InMemoryJobRepository()
    decision_repository = InMemoryDecisionRepository()

    first_result = process_source(
        source=source,
        repository=repository,
        decision_repository=decision_repository,
    )

    second_result = process_source(
        source=source,
        repository=repository,
        decision_repository=decision_repository,
    )

    assert first_result == (2, 2, 0)
    assert second_result == (0, 0, 0)

    assert len(decision_repository.decisions) == 2


def test_run_recovery_phase_submitted_result_updates_stats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from apps.worker.main import run_recovery_phase
    from packages.application.models import (
        ApplicationMethod,
        ApplicationResult,
        ApplicationStatus,
    )
    from packages.application.recovery import ApplicationRetryCandidate

    candidate = ApplicationRetryCandidate(
        job_id=1,
        application_id=10,
        method="email",
        message="retry",
    )

    class FakeRecoveryService:
        def __init__(self, repository: object) -> None:
            pass

        def build_retry_plan(self) -> list[ApplicationRetryCandidate]:
            return [candidate]

    class FakeRecoveryExecutor:
        def __init__(
            self,
            job_repository: object,
            application_repository: object,
            target_discovery: object,
            application_service: object,
        ) -> None:
            pass

        def execute(
            self,
            retry_candidate: ApplicationRetryCandidate,
        ) -> tuple[object, ApplicationResult]:
            assert retry_candidate == candidate
            return (
                object(),
                ApplicationResult(
                    status=ApplicationStatus.SUBMITTED,
                    method=ApplicationMethod.EMAIL,
                    message="retry submitted",
                ),
            )

    monkeypatch.setattr(
        "apps.worker.main.ApplicationRecoveryService",
        FakeRecoveryService,
    )
    monkeypatch.setattr(
        "apps.worker.main.ApplicationRecoveryExecutor",
        FakeRecoveryExecutor,
    )

    from packages.application.stats import ApplicationRunStats

    stats = ApplicationRunStats()

    run_recovery_phase(
        job_repository=object(),
        application_repository=object(),
        application_service=object(),
        target_discovery=object(),
        stats=stats,
    )

    assert stats.recovery_candidates == 1
    assert stats.recovery_submitted == 1
    assert stats.recovery_failed == 0
    assert stats.recovery_paused == 0
    assert stats.recovery_skipped == 0


def test_run_recovery_phase_skipped_candidate_updates_stats(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from apps.worker.main import run_recovery_phase
    from packages.application.recovery import ApplicationRetryCandidate
    from packages.application.recovery_executor import RecoveryExecutionPlan
    from packages.application.stats import ApplicationRunStats

    candidate = ApplicationRetryCandidate(
        job_id=1,
        application_id=10,
        method="email",
        message="retry",
    )

    class FakeRecoveryService:
        def __init__(self, repository: object) -> None:
            pass

        def build_retry_plan(self) -> list[ApplicationRetryCandidate]:
            return [candidate]

    class FakeRecoveryExecutor:
        def __init__(
            self,
            job_repository: object,
            application_repository: object,
            target_discovery: object,
            application_service: object,
        ) -> None:
            pass

        def execute(
            self,
            retry_candidate: ApplicationRetryCandidate,
        ) -> tuple[RecoveryExecutionPlan, None]:
            return (
                RecoveryExecutionPlan(
                    job_id=1,
                    action="skip",
                    message="target disappeared",
                ),
                None,
            )

    monkeypatch.setattr(
        "apps.worker.main.ApplicationRecoveryService",
        FakeRecoveryService,
    )
    monkeypatch.setattr(
        "apps.worker.main.ApplicationRecoveryExecutor",
        FakeRecoveryExecutor,
    )

    stats = ApplicationRunStats()

    run_recovery_phase(
        job_repository=object(),
        application_repository=object(),
        application_service=object(),
        target_discovery=object(),
        stats=stats,
    )

    assert stats.recovery_candidates == 1
    assert stats.recovery_skipped == 1
    assert stats.recovery_submitted == 0


def test_run_recovery_phase_continues_after_candidate_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from apps.worker.main import run_recovery_phase
    from packages.application.models import (
        ApplicationMethod,
        ApplicationResult,
        ApplicationStatus,
    )
    from packages.application.recovery import ApplicationRetryCandidate
    from packages.application.stats import ApplicationRunStats

    candidates = [
        ApplicationRetryCandidate(
            job_id=1,
            application_id=10,
            method="email",
            message="retry",
        ),
        ApplicationRetryCandidate(
            job_id=2,
            application_id=20,
            method="email",
            message="retry",
        ),
    ]

    class FakeRecoveryService:
        def __init__(self, repository: object) -> None:
            pass

        def build_retry_plan(self) -> list[ApplicationRetryCandidate]:
            return candidates

    class FakeRecoveryExecutor:
        def __init__(
            self,
            job_repository: object,
            application_repository: object,
            target_discovery: object,
            application_service: object,
        ) -> None:
            self.calls: list[int] = []

        def execute(
            self,
            retry_candidate: ApplicationRetryCandidate,
        ) -> tuple[object, ApplicationResult]:
            self.calls.append(retry_candidate.job_id)

            if retry_candidate.job_id == 1:
                raise RuntimeError("temporary executor failure")

            return (
                object(),
                ApplicationResult(
                    status=ApplicationStatus.SUBMITTED,
                    method=ApplicationMethod.EMAIL,
                    message="retry submitted",
                ),
            )

    executor_instances: list[FakeRecoveryExecutor] = []

    original_executor = FakeRecoveryExecutor

    def make_executor(
        job_repository: object,
        application_repository: object,
        target_discovery: object,
        application_service: object,
    ) -> FakeRecoveryExecutor:
        executor = original_executor(
            job_repository,
            application_repository,
            target_discovery,
            application_service,
        )
        executor_instances.append(executor)
        return executor

    monkeypatch.setattr(
        "apps.worker.main.ApplicationRecoveryService",
        FakeRecoveryService,
    )
    monkeypatch.setattr(
        "apps.worker.main.ApplicationRecoveryExecutor",
        make_executor,
    )

    stats = ApplicationRunStats()

    run_recovery_phase(
        job_repository=object(),
        application_repository=object(),
        application_service=object(),
        target_discovery=object(),
        stats=stats,
    )

    assert stats.recovery_candidates == 2
    assert stats.recovery_failed == 1
    assert stats.recovery_submitted == 1
    assert executor_instances[0].calls == [1, 2]
