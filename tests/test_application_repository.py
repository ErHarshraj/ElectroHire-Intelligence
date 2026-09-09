from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from packages.application.models import ApplicationMethod, ApplicationStatus
from packages.persistence.application_repository import ApplicationRecord
from packages.persistence.models import Base, JobModel
from packages.persistence.sqlalchemy_application_repository import (
    SQLAlchemyApplicationRepository,
)


def make_repository() -> tuple[Session, SQLAlchemyApplicationRepository]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)

    session.add(
        JobModel(
            title="Hardware Engineer",
            company="Test Company",
            source="test",
            source_job_id="job-1",
            source_url="https://example.com/jobs/1",
            skills="pcb, embedded",
            discovered_at=datetime.now(timezone.utc),
        )
    )
    session.commit()

    return session, SQLAlchemyApplicationRepository(session)


def make_record(
    status: ApplicationStatus,
    *,
    job_id: int = 1,
) -> ApplicationRecord:
    return ApplicationRecord(
        job_id=job_id,
        method=ApplicationMethod.EMAIL,
        status=status,
        recruiter_email="careers@example.com",
        message=f"status={status.value}",
        started_at=datetime.now(timezone.utc),
    )


def test_get_by_status_returns_matching_attempts() -> None:
    session, repository = make_repository()

    repository.save(make_record(ApplicationStatus.FAILED))
    repository.save(make_record(ApplicationStatus.SUBMITTED))
    repository.save(make_record(ApplicationStatus.FAILED))

    failed = repository.get_by_status(ApplicationStatus.FAILED)

    assert len(failed) == 2
    assert all(
        record.status == ApplicationStatus.FAILED
        for record in failed
    )

    session.close()


def test_list_active_attempts_returns_pending_in_progress_and_paused() -> None:
    session, repository = make_repository()

    repository.save(make_record(ApplicationStatus.PENDING))
    repository.save(make_record(ApplicationStatus.IN_PROGRESS))
    repository.save(make_record(ApplicationStatus.PAUSED))
    repository.save(make_record(ApplicationStatus.FAILED))
    repository.save(make_record(ApplicationStatus.SUBMITTED))

    active = repository.list_active_attempts()

    assert len(active) == 3
    assert [record.status for record in active] == [
        ApplicationStatus.PENDING,
        ApplicationStatus.IN_PROGRESS,
        ApplicationStatus.PAUSED,
    ]

    session.close()


def test_list_retryable_attempts_returns_failed_attempts_only() -> None:
    session, repository = make_repository()

    repository.save(make_record(ApplicationStatus.FAILED))
    repository.save(make_record(ApplicationStatus.PAUSED))
    repository.save(make_record(ApplicationStatus.SUBMITTED))

    retryable = repository.list_retryable_attempts()

    assert len(retryable) == 1
    assert retryable[0].status == ApplicationStatus.FAILED

    session.close()


def test_active_attempts_are_ordered_by_application_id() -> None:
    session, repository = make_repository()

    first_id = repository.save(make_record(ApplicationStatus.PAUSED))
    second_id = repository.save(make_record(ApplicationStatus.PENDING))

    active = repository.list_active_attempts()

    assert [record.id for record in active] == [first_id, second_id]

    session.close()


def test_get_by_status_preserves_application_data() -> None:
    session, repository = make_repository()

    application_id = repository.save(
        ApplicationRecord(
            job_id=1,
            method=ApplicationMethod.EMAIL,
            status=ApplicationStatus.FAILED,
            recruiter_email="recruiter@example.com",
            apply_url="https://example.com/apply",
            external_reference="EXT-123",
            message="SMTP connection failed",
        )
    )

    records = repository.get_by_status(ApplicationStatus.FAILED)

    assert len(records) == 1
    record = records[0]

    assert record.id == application_id
    assert record.job_id == 1
    assert record.method == ApplicationMethod.EMAIL
    assert record.recruiter_email == "recruiter@example.com"
    assert record.apply_url == "https://example.com/apply"
    assert record.external_reference == "EXT-123"
    assert record.message == "SMTP connection failed"

    session.close()
