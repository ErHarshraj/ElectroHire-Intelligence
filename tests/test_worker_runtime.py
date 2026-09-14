from datetime import datetime, timezone

import pytest

from apps.worker.main import ScheduledWorker
from packages.application.stats import ApplicationRunStats
from packages.common.config import Settings
from packages.observability.models import WorkerRunReport


class FakeSession:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeCycle:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.run_count = 0

    def run_cycle(self) -> WorkerRunReport:
        self.run_count += 1

        if self.should_fail:
            raise RuntimeError("cycle failed")

        now = datetime.now(timezone.utc)

        return WorkerRunReport(
            started_at=now,
            completed_at=now,
            success=True,
            queries_processed=0,
            new_jobs=0,
            evaluated_jobs=0,
            ignored_jobs=0,
            application_stats=ApplicationRunStats(),
        )


class FakeWorkerRunRepository:
    def __init__(self, session: FakeSession) -> None:
        self.session = session

    @staticmethod
    def from_report(report: WorkerRunReport) -> WorkerRunReport:
        return report

    def save(self, record: WorkerRunReport) -> int:
        return 1


@pytest.fixture(autouse=True)
def fake_worker_run_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "apps.worker.main.SQLAlchemyWorkerRunRepository",
        FakeWorkerRunRepository,
    )


def test_scheduled_worker_creates_and_closes_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    cycle = FakeCycle()

    monkeypatch.setattr(
        "apps.worker.main.SessionLocal",
        lambda: session,
    )
    monkeypatch.setattr(
        "apps.worker.main.build_worker_cycle",
        lambda settings, session: cycle,
    )

    worker = ScheduledWorker(settings=Settings())

    worker.run_cycle()

    assert cycle.run_count == 1
    assert session.closed is True


def test_scheduled_worker_closes_session_when_cycle_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = FakeSession()
    cycle = FakeCycle(should_fail=True)

    monkeypatch.setattr(
        "apps.worker.main.SessionLocal",
        lambda: session,
    )
    monkeypatch.setattr(
        "apps.worker.main.build_worker_cycle",
        lambda settings, session: cycle,
    )

    worker = ScheduledWorker(settings=Settings())

    with pytest.raises(RuntimeError, match="cycle failed"):
        worker.run_cycle()

    assert cycle.run_count == 1
    assert session.closed is True


def test_scheduled_worker_uses_fresh_session_for_each_cycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sessions: list[FakeSession] = []
    cycles: list[FakeCycle] = []

    def create_session() -> FakeSession:
        session = FakeSession()
        sessions.append(session)
        return session

    def build_cycle(settings: Settings, session: FakeSession) -> FakeCycle:
        cycle = FakeCycle()
        cycles.append(cycle)
        return cycle

    monkeypatch.setattr(
        "apps.worker.main.SessionLocal",
        create_session,
    )
    monkeypatch.setattr(
        "apps.worker.main.build_worker_cycle",
        build_cycle,
    )

    worker = ScheduledWorker(settings=Settings())

    worker.run_cycle()
    worker.run_cycle()

    assert len(sessions) == 2
    assert len(cycles) == 2
    assert sessions[0] is not sessions[1]
    assert all(session.closed for session in sessions)
    assert all(cycle.run_count == 1 for cycle in cycles)


def test_build_application_service_uses_dry_run_browser_by_default() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from apps.worker.main import build_application_service
    from packages.application.adapters.dry_run import DryRunApplicationAdapter
    from packages.persistence.models import Base
    from packages.persistence.sqlalchemy_application_repository import (
        SQLAlchemyApplicationRepository,
    )

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    repository = SQLAlchemyApplicationRepository(Session(engine))
    service = build_application_service(
        settings=Settings(browser_enabled=False),
        application_repository=repository,
    )

    assert isinstance(service.browser_adapter, DryRunApplicationAdapter)


def test_build_application_service_uses_browser_adapter_when_enabled(
    tmp_path,
) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from apps.worker.main import build_application_service
    from packages.application.adapters.browser import BrowserApplicationAdapter
    from packages.persistence.models import Base
    from packages.persistence.sqlalchemy_application_repository import (
        SQLAlchemyApplicationRepository,
    )

    resume_path = tmp_path / "resume.pdf"
    resume_path.write_bytes(b"%PDF-1.4 test resume")

    settings = Settings(
        browser_enabled=True,
        candidate_email="harshraj.test@example.com",
        candidate_phone="9876543210",
        candidate_resume_path=str(resume_path),
    )

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    repository = SQLAlchemyApplicationRepository(Session(engine))
    service = build_application_service(
        settings=settings,
        application_repository=repository,
    )

    assert isinstance(service.browser_adapter, BrowserApplicationAdapter)
    assert service.browser_adapter.candidate is not None
    assert service.browser_adapter.candidate.email == (
        "harshraj.test@example.com"
    )
    assert service.browser_adapter.candidate.phone == "9876543210"
    assert service.browser_adapter.candidate.resume_path == str(resume_path)


def test_build_application_service_rejects_missing_browser_resume(
) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from apps.worker.main import build_application_service
    from packages.persistence.models import Base
    from packages.persistence.sqlalchemy_application_repository import (
        SQLAlchemyApplicationRepository,
    )

    settings = Settings(
        browser_enabled=True,
        candidate_email="harshraj.test@example.com",
        candidate_phone="9876543210",
        candidate_resume_path="/tmp/electrohire-missing-resume.pdf",
    )

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    repository = SQLAlchemyApplicationRepository(Session(engine))

    with pytest.raises(
        RuntimeError,
        match="Candidate resume not found",
    ):
        build_application_service(
            settings=settings,
            application_repository=repository,
        )
