from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from packages.application.career_models import (
    CareerApplicationRecord,
    CareerApplicationStatus,
)
from packages.persistence.models import Base
from packages.persistence.sqlalchemy_career_application_repository import (
    SQLAlchemyCareerApplicationRepository,
)


def make_repository() -> SQLAlchemyCareerApplicationRepository:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    return SQLAlchemyCareerApplicationRepository(Session(engine))


def make_record(
    *,
    job_id: int = 1,
    status: CareerApplicationStatus = CareerApplicationStatus.SHORTLISTED,
) -> CareerApplicationRecord:
    return CareerApplicationRecord(
        job_id=job_id,
        status=status,
        application_url="https://example.com/apply",
        notes="initial shortlist",
    )


def test_save_and_get_application() -> None:
    repository = make_repository()

    application_id = repository.save(make_record())

    record = repository.get(application_id)

    assert record is not None
    assert record.id == application_id
    assert record.job_id == 1
    assert record.status == CareerApplicationStatus.SHORTLISTED
    assert record.application_url == "https://example.com/apply"
    assert record.notes == "initial shortlist"
    assert record.created_at is not None
    assert record.updated_at is not None


def test_get_missing_application_returns_none() -> None:
    repository = make_repository()

    assert repository.get(999) is None


def test_get_by_job() -> None:
    repository = make_repository()

    repository.save(make_record(job_id=42))

    record = repository.get_by_job(42)

    assert record is not None
    assert record.job_id == 42
    assert record.status == CareerApplicationStatus.SHORTLISTED


def test_get_by_different_job_returns_none() -> None:
    repository = make_repository()

    repository.save(make_record(job_id=42))

    assert repository.get_by_job(99) is None


def test_list_by_status() -> None:
    repository = make_repository()

    repository.save(
        make_record(
            job_id=1,
            status=CareerApplicationStatus.APPLIED,
        )
    )
    repository.save(
        make_record(
            job_id=2,
            status=CareerApplicationStatus.SCREENING,
        )
    )
    repository.save(
        make_record(
            job_id=3,
            status=CareerApplicationStatus.APPLIED,
        )
    )

    applications = repository.list_by_status(
        CareerApplicationStatus.APPLIED
    )

    assert len(applications) == 2
    assert [application.job_id for application in applications] == [1, 3]


def test_update_application() -> None:
    repository = make_repository()

    application_id = repository.save(make_record())

    applied_at = datetime.now(timezone.utc)

    repository.update(
        application_id,
        status=CareerApplicationStatus.APPLIED,
        application_url="https://example.com/new-apply",
        applied_at=applied_at,
        notes="application submitted",
        next_followup_at=applied_at,
    )

    record = repository.get(application_id)

    assert record is not None
    assert record.status == CareerApplicationStatus.APPLIED
    assert record.application_url == "https://example.com/new-apply"
    assert record.applied_at == applied_at
    assert record.notes == "application submitted"
    assert record.next_followup_at == applied_at


def test_update_missing_application_raises() -> None:
    repository = make_repository()

    try:
        repository.update(
            999,
            status=CareerApplicationStatus.APPLIED,
        )
    except ValueError as exc:
        assert str(exc) == "career application 999 does not exist"
    else:
        raise AssertionError("expected ValueError")


def test_one_career_application_per_job() -> None:
    repository = make_repository()

    repository.save(make_record(job_id=42))

    try:
        repository.save(make_record(job_id=42))
    except Exception as exc:
        assert "UNIQUE" in str(exc).upper()
    else:
        raise AssertionError(
            "expected duplicate job_id to violate the unique constraint"
        )
