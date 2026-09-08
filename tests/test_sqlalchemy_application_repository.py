from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from packages.application.models import (
    ApplicationMethod,
    ApplicationStatus,
)
from packages.persistence.application_repository import ApplicationRecord
from packages.persistence.models import Base
from packages.persistence.sqlalchemy_application_repository import (
    SQLAlchemyApplicationRepository,
)


def make_repository() -> SQLAlchemyApplicationRepository:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    return SQLAlchemyApplicationRepository(Session(engine))


def test_save_application() -> None:
    repository = make_repository()

    record = ApplicationRecord(
        job_id=1,
        method=ApplicationMethod.BROWSER,
        status=ApplicationStatus.PENDING,
        apply_url="https://example.com/apply/123",
        message="application ready",
    )

    repository.save(record)

    assert repository.has_submitted_application(1) is False


def test_submitted_application_is_detected() -> None:
    repository = make_repository()

    record = ApplicationRecord(
        job_id=1,
        method=ApplicationMethod.EMAIL,
        status=ApplicationStatus.SUBMITTED,
        recruiter_email="recruiter@example.com",
        message="email submitted",
        submitted_at=datetime.now(timezone.utc),
    )

    repository.save(record)

    assert repository.has_submitted_application(1) is True


def test_different_job_is_not_marked_submitted() -> None:
    repository = make_repository()

    record = ApplicationRecord(
        job_id=1,
        method=ApplicationMethod.EMAIL,
        status=ApplicationStatus.SUBMITTED,
    )

    repository.save(record)

    assert repository.has_submitted_application(2) is False
