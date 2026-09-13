from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from packages.application.models import (
    ApplicationApprovalStatus,
    ApplicationMethod,
)
from packages.persistence.application_approval_repository import ApplicationApprovalRecord
from packages.persistence.models import Base
from packages.persistence.sqlalchemy_application_approval_repository import (
    SQLAlchemyApplicationApprovalRepository,
)


def make_record() -> ApplicationApprovalRecord:
    return ApplicationApprovalRecord(
        job_id=1,
        source="adzuna",
        source_job_id="approval-sql-001",
        job_title="Embedded Hardware Engineer",
        company="Example Electronics",
        method=ApplicationMethod.EMAIL,
        status=ApplicationApprovalStatus.PENDING,
        recruiter_email="careers@example.com",
        reason="explicit approval required",
        created_at=datetime.now(timezone.utc),
    )


def test_sqlalchemy_approval_repository_persists_and_transitions() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        repository = SQLAlchemyApplicationApprovalRepository(session)
        approval_id = repository.save(make_record())

        pending = repository.get(approval_id)
        assert pending is not None
        assert pending.status == ApplicationApprovalStatus.PENDING
        assert repository.get_pending(1) is not None
        assert len(repository.list_pending()) == 1

        repository.approve(approval_id, datetime.now(timezone.utc))
        approved = repository.get(approval_id)
        assert approved is not None
        assert approved.status == ApplicationApprovalStatus.APPROVED
        assert repository.get_pending(1) is None
        assert len(repository.list_approved()) == 1


def test_sqlalchemy_approval_repository_rejects_non_pending_transition() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        repository = SQLAlchemyApplicationApprovalRepository(session)
        approval_id = repository.save(make_record())
        repository.reject(approval_id, datetime.now(timezone.utc))

        try:
            repository.reject(approval_id, datetime.now(timezone.utc))
        except ValueError as exc:
            assert "not pending" in str(exc)
        else:
            raise AssertionError("expected rejection of a non-pending approval")
