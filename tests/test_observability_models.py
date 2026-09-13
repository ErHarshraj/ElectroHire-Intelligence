from datetime import datetime, timedelta, timezone

from packages.application.stats import ApplicationRunStats
from packages.observability.models import WorkerRunReport


def test_worker_run_report_stores_run_information() -> None:
    started_at = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
    completed_at = started_at + timedelta(seconds=12.5)

    stats = ApplicationRunStats()
    stats.apply_decisions = 3
    stats.submitted = 2
    stats.failed = 1

    report = WorkerRunReport(
        started_at=started_at,
        completed_at=completed_at,
        success=True,
        queries_processed=4,
        new_jobs=10,
        evaluated_jobs=8,
        ignored_jobs=2,
        application_stats=stats,
    )

    assert report.started_at == started_at
    assert report.completed_at == completed_at
    assert report.success is True

    assert report.queries_processed == 4
    assert report.new_jobs == 10
    assert report.evaluated_jobs == 8
    assert report.ignored_jobs == 2

    assert report.application_stats.apply_decisions == 3
    assert report.application_stats.submitted == 2
    assert report.application_stats.failed == 1

    assert report.error is None
    assert report.duration_seconds == 12.5


def test_worker_run_report_can_store_failure() -> None:
    started_at = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
    completed_at = started_at + timedelta(seconds=3)

    report = WorkerRunReport(
        started_at=started_at,
        completed_at=completed_at,
        success=False,
        queries_processed=1,
        new_jobs=0,
        evaluated_jobs=0,
        ignored_jobs=0,
        application_stats=ApplicationRunStats(),
        error="Adzuna request failed",
    )

    assert report.success is False
    assert report.error == "Adzuna request failed"
    assert report.duration_seconds == 3.0
