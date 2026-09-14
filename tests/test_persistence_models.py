from datetime import datetime, timezone

from sqlalchemy import inspect

from packages.persistence.models import Base, WorkerRunModel


def test_worker_run_model_has_expected_table() -> None:
    assert WorkerRunModel.__tablename__ == "worker_runs"


def test_worker_run_model_is_registered_with_base() -> None:
    assert "worker_runs" in Base.metadata.tables


def test_worker_run_model_has_expected_columns() -> None:
    columns = {
        column.name
        for column in inspect(WorkerRunModel).columns
    }

    expected_columns = {
        "id",
        "started_at",
        "completed_at",
        "success",
        "queries_processed",
        "new_jobs",
        "evaluated_jobs",
        "ignored_jobs",
        "apply_decisions",
        "targets_found",
        "no_target",
        "submitted",
        "pending",
        "failed",
        "paused",
        "already_submitted",
        "recovery_candidates",
        "recovery_submitted",
        "recovery_failed",
        "recovery_paused",
        "recovery_skipped",
        "error",
    }

    assert columns == expected_columns


def test_worker_run_model_can_be_constructed() -> None:
    started_at = datetime.now(timezone.utc)
    completed_at = datetime.now(timezone.utc)

    worker_run = WorkerRunModel(
        started_at=started_at,
        completed_at=completed_at,
        success=True,
        queries_processed=2,
        new_jobs=10,
        evaluated_jobs=8,
        ignored_jobs=2,
        apply_decisions=3,
        targets_found=2,
        no_target=1,
        submitted=1,
        pending=1,
        failed=0,
        paused=0,
        already_submitted=0,
        recovery_candidates=2,
        recovery_submitted=1,
        recovery_failed=0,
        recovery_paused=0,
        recovery_skipped=1,
        error=None,
    )

    assert worker_run.started_at == started_at
    assert worker_run.completed_at == completed_at
    assert worker_run.success is True
    assert worker_run.new_jobs == 10
    assert worker_run.submitted == 1
    assert worker_run.error is None
