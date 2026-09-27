from collections.abc import Generator
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from pydantic import HttpUrl
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.main import app, get_db
from packages.application.stats import ApplicationRunStats
from packages.domain.candidate_profile import CandidateProfile
from packages.domain.job import Job
from packages.persistence.models import Base
from packages.persistence.sqlalchemy_candidate_profile_repository import (
    SQLAlchemyCandidateProfileRepository,
)
from packages.persistence.sqlalchemy_job_repository import (
    SQLAlchemyJobRepository,
)
from packages.persistence.sqlalchemy_worker_run_repository import (
    SQLAlchemyWorkerRunRepository,
)
from packages.persistence.worker_run_repository import WorkerRunRecord

TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)

Base.metadata.create_all(bind=test_engine)


def override_get_db() -> Generator[Session, None, None]:
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_jobs_returns_empty_list() -> None:
    response = client.get("/jobs")

    assert response.status_code == 200
    assert response.json() == []


def test_list_jobs_returns_relevance_information() -> None:
    session = TestSessionLocal()

    try:
        repository = SQLAlchemyJobRepository(session)

        repository.save(
            Job(
                title="Hardware Design Engineer",
                company="Test Electronics",
                location="Bangalore",
                description=(
                    "Design embedded hardware, PCB layouts, "
                    "and electronic circuits."
                ),
                source="test",
                source_job_id="relevance-001",
                source_url=HttpUrl("https://example.com/jobs/relevance-001"),
                skills=["PCB", "Altium"],
                discovered_at=datetime.now(timezone.utc),
            )
        )
    finally:
        session.close()

    response = client.get("/jobs")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    job = data[0]

    assert job["title"] == "Hardware Design Engineer"
    assert job["company"] == "Test Electronics"

    assert job["relevance"]["is_relevant"] is True
    assert job["relevance"]["score"] > 0
    assert "title:hardware design engineer" in job["relevance"]["reasons"]


def test_list_jobs_uses_persisted_candidate_profile_for_ranking() -> None:
    session = TestSessionLocal()

    try:
        candidate_repository = SQLAlchemyCandidateProfileRepository(session)

        candidate_repository.save(
            CandidateProfile(
                full_name="Test Candidate",
                target_roles=("custom embedded specialist",),
                role_families=(),
                skill_families=(),
                domain_families=(),
                experience_keywords=(),
            )
        )

        job_repository = SQLAlchemyJobRepository(session)

        job_repository.save(
            Job(
                title="Custom Embedded Specialist",
                company="Profile Test Electronics",
                location="Indore",
                description="A deliberately customized profile test job.",
                source="profile-test",
                source_job_id="profile-test-001",
                source_url=HttpUrl(
                    "https://example.com/jobs/profile-test-001"
                ),
                skills=[],
                discovered_at=datetime.now(timezone.utc),
            )
        )
    finally:
        session.close()

    response = client.get("/jobs")

    assert response.status_code == 200

    data = response.json()

    returned_job = next(
        item
        for item in data
        if item["source_job_id"] == "profile-test-001"
    )

    assert "Target role match: custom embedded specialist" in (
        returned_job["ranking"]["reasons"]
    )


def test_application_approval_endpoints() -> None:
    from packages.application.approval import ApplicationApprovalService
    from packages.application.models import (
        ApplicationApprovalRequest,
        ApplicationApprovalStatus,
        ApplicationMethod,
    )
    from packages.persistence.sqlalchemy_application_approval_repository import (
        SQLAlchemyApplicationApprovalRepository,
    )

    session = TestSessionLocal()

    try:
        service = ApplicationApprovalService(
            SQLAlchemyApplicationApprovalRepository(session)
        )
        approval = service.request(
            ApplicationApprovalRequest(
                source="test",
                source_job_id="api-approval-001",
                job_title="Hardware Design Engineer",
                company="Example Electronics",
                application_method=ApplicationMethod.EMAIL,
                recruiter_email="careers@example.com",
                reason="explicit approval required",
            ),
            job_id=999,
        )
        approval_id = approval.id
    finally:
        session.close()

    response = client.get("/applications/approvals")
    assert response.status_code == 200
    assert response.json()[0]["id"] == approval_id
    assert response.json()[0]["status"] == ApplicationApprovalStatus.PENDING.value

    response = client.post(f"/applications/approvals/{approval_id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == ApplicationApprovalStatus.APPROVED.value

    response = client.get("/applications/approvals")
    assert response.status_code == 200
    assert response.json() == []


def test_list_jobs_includes_job_without_source_job_id() -> None:
    session = TestSessionLocal()

    try:
        repository = SQLAlchemyJobRepository(session)

        repository.save(
            Job(
                title="Electronics Test Engineer",
                company="Nullable ID Electronics",
                location="Indore",
                description=(
                    "Test electronics hardware, circuits, PCB assemblies, "
                    "and embedded systems."
                ),
                source="test-nullable-id",
                source_job_id=None,
                source_url=HttpUrl(
                    "https://example.com/jobs/nullable-source-id"
                ),
                skills=["PCB", "Embedded Systems"],
                discovered_at=datetime.now(timezone.utc),
            )
        )

        jobs = repository.list_jobs_with_ids()
        job_id = jobs[-1][0]
    finally:
        session.close()

    response = client.get("/jobs")

    assert response.status_code == 200

    data = response.json()

    returned_job = next(
        item
        for item in data
        if item["id"] == job_id
    )

    assert returned_job["title"] == "Electronics Test Engineer"
    assert returned_job["company"] == "Nullable ID Electronics"
    assert returned_job["source"] == "test-nullable-id"
    assert returned_job["source_job_id"] is None


def _worker_run_record(
    started_at: datetime,
    completed_at: datetime,
    *,
    success: bool = True,
    error: str | None = None,
) -> WorkerRunRecord:
    return WorkerRunRecord(
        started_at=started_at,
        completed_at=completed_at,
        success=success,
        queries_processed=4,
        new_jobs=3,
        evaluated_jobs=5,
        ignored_jobs=1,
        application_stats=ApplicationRunStats(
            apply_decisions=2,
            targets_found=2,
            no_target=0,
            submitted=1,
            pending=1,
            failed=0,
            paused=0,
            already_submitted=0,
            recovery_candidates=1,
            recovery_submitted=1,
            recovery_failed=0,
            recovery_paused=0,
            recovery_skipped=0,
        ),
        error=error,
    )


def test_list_worker_runs_returns_empty_list() -> None:
    response = client.get("/worker-runs")

    assert response.status_code == 200
    assert response.json() == []


def test_list_worker_runs_returns_newest_first_and_respects_limit() -> None:
    session = TestSessionLocal()

    try:
        repository = SQLAlchemyWorkerRunRepository(session)

        first_id = repository.save(
            _worker_run_record(
                datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
                datetime(2026, 1, 1, 10, 2, tzinfo=timezone.utc),
            )
        )
        second_id = repository.save(
            _worker_run_record(
                datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc),
                datetime(2026, 1, 1, 11, 3, tzinfo=timezone.utc),
            )
        )
    finally:
        session.close()

    response = client.get("/worker-runs?limit=1")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == second_id
    assert data[0]["id"] != first_id
    assert data[0]["duration_seconds"] == 180.0


def test_get_worker_run_returns_complete_report() -> None:
    session = TestSessionLocal()

    try:
        repository = SQLAlchemyWorkerRunRepository(session)

        worker_run_id = repository.save(
            _worker_run_record(
                datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 2, 1, 12, 5, tzinfo=timezone.utc),
                success=False,
                error="simulated worker failure",
            )
        )
    finally:
        session.close()

    response = client.get(f"/worker-runs/{worker_run_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == worker_run_id
    assert data["success"] is False
    assert data["queries_processed"] == 4
    assert data["new_jobs"] == 3
    assert data["evaluated_jobs"] == 5
    assert data["ignored_jobs"] == 1
    assert data["duration_seconds"] == 300.0
    assert data["error"] == "simulated worker failure"

    stats = data["application_stats"]

    assert stats["apply_decisions"] == 2
    assert stats["targets_found"] == 2
    assert stats["no_target"] == 0
    assert stats["submitted"] == 1
    assert stats["pending"] == 1
    assert stats["failed"] == 0
    assert stats["paused"] == 0
    assert stats["already_submitted"] == 0
    assert stats["recovery_candidates"] == 1
    assert stats["recovery_submitted"] == 1
    assert stats["recovery_failed"] == 0
    assert stats["recovery_paused"] == 0
    assert stats["recovery_skipped"] == 0


def test_get_worker_run_returns_404_for_missing_id() -> None:
    response = client.get("/worker-runs/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Worker run not found"}


def test_list_worker_runs_rejects_non_positive_limit() -> None:
    response = client.get("/worker-runs?limit=0")

    assert response.status_code == 400
    assert response.json() == {
        "detail": "limit must be greater than zero"
    }
