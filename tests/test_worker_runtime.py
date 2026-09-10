import pytest

from apps.worker.main import ScheduledWorker
from packages.common.config import Settings


class FakeSession:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeCycle:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.run_count = 0

    def run_cycle(self) -> None:
        self.run_count += 1

        if self.should_fail:
            raise RuntimeError("cycle failed")


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
