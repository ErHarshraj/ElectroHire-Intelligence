from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.application.stats import ApplicationRunStats
from packages.observability.models import WorkerRunReport
from packages.persistence.models import WorkerRunModel
from packages.persistence.worker_run_repository import (
    WorkerRunRecord,
    WorkerRunRepository,
)


class SQLAlchemyWorkerRunRepository(WorkerRunRepository):
    """SQLAlchemy persistence for worker run reports."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, record: WorkerRunRecord) -> int:
        """Create and persist a worker run."""

        stats = record.application_stats

        worker_run = WorkerRunModel(
            started_at=record.started_at,
            completed_at=record.completed_at,
            success=record.success,
            queries_processed=record.queries_processed,
            new_jobs=record.new_jobs,
            evaluated_jobs=record.evaluated_jobs,
            ignored_jobs=record.ignored_jobs,
            apply_decisions=stats.apply_decisions,
            targets_found=stats.targets_found,
            no_target=stats.no_target,
            submitted=stats.submitted,
            pending=stats.pending,
            failed=stats.failed,
            paused=stats.paused,
            already_submitted=stats.already_submitted,
            recovery_candidates=stats.recovery_candidates,
            recovery_submitted=stats.recovery_submitted,
            recovery_failed=stats.recovery_failed,
            recovery_paused=stats.recovery_paused,
            recovery_skipped=stats.recovery_skipped,
            error=record.error,
        )

        self.session.add(worker_run)
        self.session.flush()

        worker_run_id = worker_run.id

        self.session.commit()

        return worker_run_id

    def get_by_id(
        self,
        worker_run_id: int,
    ) -> WorkerRunRecord | None:
        """Return a worker run by ID."""

        worker_run = self.session.get(
            WorkerRunModel,
            worker_run_id,
        )

        if worker_run is None:
            return None

        return self._to_record(worker_run)

    def list_recent(
        self,
        limit: int = 20,
    ) -> list[WorkerRunRecord]:
        """Return the most recent worker runs."""

        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        statement = (
            select(WorkerRunModel)
            .order_by(WorkerRunModel.id.desc())
            .limit(limit)
        )

        worker_runs = self.session.scalars(statement).all()

        return [
            self._to_record(worker_run)
            for worker_run in worker_runs
        ]

    @staticmethod
    def _to_record(
        worker_run: WorkerRunModel,
    ) -> WorkerRunRecord:
        """Convert a database model into a persistence record."""

        application_stats = ApplicationRunStats(
            apply_decisions=worker_run.apply_decisions,
            targets_found=worker_run.targets_found,
            no_target=worker_run.no_target,
            submitted=worker_run.submitted,
            pending=worker_run.pending,
            failed=worker_run.failed,
            paused=worker_run.paused,
            already_submitted=worker_run.already_submitted,
            recovery_candidates=worker_run.recovery_candidates,
            recovery_submitted=worker_run.recovery_submitted,
            recovery_failed=worker_run.recovery_failed,
            recovery_paused=worker_run.recovery_paused,
            recovery_skipped=worker_run.recovery_skipped,
        )

        return WorkerRunRecord(
            started_at=SQLAlchemyWorkerRunRepository._as_utc(
                worker_run.started_at,
            ),
            completed_at=SQLAlchemyWorkerRunRepository._as_utc(
                worker_run.completed_at,
            ),
            success=worker_run.success,
            queries_processed=worker_run.queries_processed,
            new_jobs=worker_run.new_jobs,
            evaluated_jobs=worker_run.evaluated_jobs,
            ignored_jobs=worker_run.ignored_jobs,
            application_stats=application_stats,
            error=worker_run.error,
            id=worker_run.id,
        )

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        """Return a timezone-aware UTC datetime."""

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    @staticmethod
    def from_report(
        report: WorkerRunReport,
    ) -> WorkerRunRecord:
        """Convert a worker run report into a persistence record."""

        return WorkerRunRecord(
            started_at=report.started_at,
            completed_at=report.completed_at,
            success=report.success,
            queries_processed=report.queries_processed,
            new_jobs=report.new_jobs,
            evaluated_jobs=report.evaluated_jobs,
            ignored_jobs=report.ignored_jobs,
            application_stats=report.application_stats,
            error=report.error,
        )
