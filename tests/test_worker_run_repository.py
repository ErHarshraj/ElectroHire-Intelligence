from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from packages.application.stats import ApplicationRunStats
from packages.observability.models import WorkerRunReport
from packages.persistence.models import Base
from packages.persistence.sqlalchemy_worker_run_repository import (
    SQLAlchemyWorkerRunRepository,
)
from packages.persistence.worker_run_repository import WorkerRunRecord


def build_record(
    *,
    started_at: datetime,
    offset_seconds: int = 10,
    success: bool = True,
    error: str | None = None,
) -> WorkerRunRecord:
    stats = ApplicationRunStats(
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
    )

    return WorkerRunRecord(
        started_at=started_at,
        completed_at=started_at + timedelta(
            seconds=offset_seconds,
        ),
        success=success,
        queries_processed=2,
        new_jobs=10,
        evaluated_jobs=8,
        ignored_jobs=2,
        application_stats=stats,
        error=error,
    )


def test_save_and_get_by_id() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    started_at = datetime.now(timezone.utc)
    record = build_record(started_at=started_at)

    with Session(engine) as session:
        repository = SQLAlchemyWorkerRunRepository(session)

        worker_run_id = repository.save(record)

        assert worker_run_id > 0

        saved = repository.get_by_id(worker_run_id)

        assert saved is not None
        assert saved.id == worker_run_id
        assert saved.started_at == record.started_at
        assert saved.completed_at == record.completed_at
        assert saved.success is True
        assert saved.queries_processed == 2
        assert saved.new_jobs == 10
        assert saved.evaluated_jobs == 8
        assert saved.ignored_jobs == 2
        assert saved.application_stats == record.application_stats
        assert saved.error is None


def test_failed_run_and_error_round_trip() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    started_at = datetime.now(timezone.utc)
    record = build_record(
        started_at=started_at,
        success=False,
        error="database connection failed",
    )

    with Session(engine) as session:
        repository = SQLAlchemyWorkerRunRepository(session)

        worker_run_id = repository.save(record)
        saved = repository.get_by_id(worker_run_id)

        assert saved is not None
        assert saved.success is False
        assert saved.error == "database connection failed"


def test_get_by_id_returns_none_for_missing_run() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        repository = SQLAlchemyWorkerRunRepository(session)

        assert repository.get_by_id(9999) is None


def test_list_recent_returns_newest_runs_first() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    started_at = datetime.now(timezone.utc)

    with Session(engine) as session:
        repository = SQLAlchemyWorkerRunRepository(session)

        first_id = repository.save(
            build_record(
                started_at=started_at,
            )
        )

        second_id = repository.save(
            build_record(
                started_at=started_at + timedelta(minutes=1),
            )
        )

        third_id = repository.save(
            build_record(
                started_at=started_at + timedelta(minutes=2),
            )
        )

        recent = repository.list_recent()

        assert [record.id for record in recent] == [
            third_id,
            second_id,
            first_id,
        ]


def test_list_recent_respects_limit() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    started_at = datetime.now(timezone.utc)

    with Session(engine) as session:
        repository = SQLAlchemyWorkerRunRepository(session)

        for offset in range(5):
            repository.save(
                build_record(
                    started_at=started_at + timedelta(
                        minutes=offset,
                    ),
                )
            )

        recent = repository.list_recent(limit=2)

        assert len(recent) == 2


def test_list_recent_rejects_invalid_limit() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        repository = SQLAlchemyWorkerRunRepository(session)

        with pytest.raises(
            ValueError,
            match="limit must be greater than zero",
        ):
            repository.list_recent(limit=0)


def test_from_report_converts_worker_report() -> None:
    started_at = datetime.now(timezone.utc)

    stats = ApplicationRunStats(
        apply_decisions=5,
        targets_found=4,
        no_target=1,
        submitted=2,
        pending=1,
        failed=1,
        paused=0,
        already_submitted=0,
        recovery_candidates=3,
        recovery_submitted=2,
        recovery_failed=1,
        recovery_paused=0,
        recovery_skipped=0,
    )

    report = WorkerRunReport(
        started_at=started_at,
        completed_at=started_at + timedelta(seconds=25),
        success=False,
        queries_processed=4,
        new_jobs=20,
        evaluated_jobs=15,
        ignored_jobs=5,
        application_stats=stats,
        error="test worker failure",
    )

    record = SQLAlchemyWorkerRunRepository.from_report(report)

    assert record.started_at == report.started_at
    assert record.completed_at == report.completed_at
    assert record.success == report.success
    assert record.queries_processed == report.queries_processed
    assert record.new_jobs == report.new_jobs
    assert record.evaluated_jobs == report.evaluated_jobs
    assert record.ignored_jobs == report.ignored_jobs
    assert record.application_stats == report.application_stats
    assert record.error == report.error
    assert record.id is None
