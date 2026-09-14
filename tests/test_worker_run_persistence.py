from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.worker.main import ScheduledWorker
from packages.application.stats import ApplicationRunStats
from packages.common.config import Settings
from packages.observability.models import WorkerRunReport
from packages.persistence.models import Base
from packages.persistence.sqlalchemy_worker_run_repository import (
    SQLAlchemyWorkerRunRepository,
)


def test_scheduled_worker_persists_worker_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    monkeypatch.setattr(
        "apps.worker.main.SessionLocal",
        Session,
    )

    started_at = datetime.now(timezone.utc)
    completed_at = datetime.now(timezone.utc)

    expected_report = WorkerRunReport(
        started_at=started_at,
        completed_at=completed_at,
        success=True,
        queries_processed=2,
        new_jobs=5,
        evaluated_jobs=4,
        ignored_jobs=1,
        application_stats=ApplicationRunStats(
            apply_decisions=2,
            targets_found=2,
            submitted=1,
        ),
    )

    class FakeCycle:
        def run_cycle(self) -> WorkerRunReport:
            return expected_report

    monkeypatch.setattr(
        "apps.worker.main.build_worker_cycle",
        lambda **kwargs: FakeCycle(),
    )

    settings = Settings(
        adzuna_app_id="test-app-id",
        adzuna_app_key="test-app-key",
        adzuna_queries=["hardware engineer"],
        adzuna_pages=1,
    )

    worker = ScheduledWorker(settings)
    report = worker.run_cycle()

    assert report == expected_report

    session = Session()

    try:
        repository = SQLAlchemyWorkerRunRepository(session)
        records = repository.list_recent()

        assert len(records) == 1

        record = records[0]

        assert record.success is True
        assert record.queries_processed == 2
        assert record.new_jobs == 5
        assert record.evaluated_jobs == 4
        assert record.ignored_jobs == 1

        assert record.application_stats.apply_decisions == 2
        assert record.application_stats.targets_found == 2
        assert record.application_stats.submitted == 1
    finally:
        session.close()
