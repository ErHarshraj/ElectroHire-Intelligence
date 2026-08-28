from datetime import datetime, timezone

from pydantic import HttpUrl
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from packages.domain.job import Job
from packages.persistence.models import Base
from packages.persistence.sqlalchemy_job_repository import (
    SQLAlchemyJobRepository,
)


def create_test_job(source_job_id: str) -> Job:
    return Job(
        title="Embedded Hardware Engineer",
        company="Example Electronics",
        location="Bengaluru, India",
        description="Design embedded hardware and PCB systems.",
        source="mock",
        source_job_id=source_job_id,
        source_url=HttpUrl(
            f"https://example.com/jobs/{source_job_id}"
        ),
        employment_type="Full-time",
        experience_required="0-2 years",
        skills=["Embedded C", "PCB Design", "STM32"],
        posted_at=datetime(2026, 8, 28, tzinfo=timezone.utc),
        discovered_at=datetime(2026, 8, 28, tzinfo=timezone.utc),
    )


def create_repository() -> tuple[Session, SQLAlchemyJobRepository]:
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    session = Session(engine)

    return session, SQLAlchemyJobRepository(session)


def test_save_and_get_job() -> None:
    session, repository = create_repository()

    job = create_test_job("JOB-001")

    repository.save(job)

    result = repository.get_by_source_job_id(
        "mock",
        "JOB-001",
    )

    assert result is not None
    assert result.title == job.title
    assert result.company == job.company
    assert result.source_job_id == "JOB-001"
    assert result.source_url == job.source_url
    assert result.skills == job.skills

    session.close()


def test_get_missing_job_returns_none() -> None:
    session, repository = create_repository()

    result = repository.get_by_source_job_id(
        "mock",
        "DOES-NOT-EXIST",
    )

    assert result is None

    session.close()


def test_list_jobs() -> None:
    session, repository = create_repository()

    job_1 = create_test_job("JOB-001")
    job_2 = create_test_job("JOB-002")

    repository.save(job_1)
    repository.save(job_2)

    jobs = repository.list_jobs()

    assert len(jobs) == 2
    assert jobs[0].source_job_id == "JOB-001"
    assert jobs[1].source_job_id == "JOB-002"

    session.close()

def test_save_existing_job_updates_record() -> None:
    session, repository = create_repository()

    original_job = create_test_job("JOB-001")
    repository.save(original_job)

    updated_job = original_job.model_copy(
        update={
            "title": "Senior Embedded Hardware Engineer",
            "company": "Updated Electronics",
            "skills": ["STM32", "CAN", "PCB Design"],
        }
    )

    repository.save(updated_job)

    jobs = repository.list_jobs()

    assert len(jobs) == 1
    assert jobs[0].title == "Senior Embedded Hardware Engineer"
    assert jobs[0].company == "Updated Electronics"
    assert jobs[0].skills == ["STM32", "CAN", "PCB Design"]

    session.close()


def test_save_same_source_job_id_does_not_create_duplicate() -> None:
    session, repository = create_repository()

    job = create_test_job("JOB-001")

    repository.save(job)
    repository.save(job)

    jobs = repository.list_jobs()

    assert len(jobs) == 1
    assert jobs[0].source == "mock"
    assert jobs[0].source_job_id == "JOB-001"

    session.close()

def test_save_updates_existing_job() -> None:
    session, repository = create_repository()

    original = create_test_job("JOB-001")
    repository.save(original)

    updated = original.model_copy(
        update={
            "title": "Senior Embedded Hardware Engineer",
            "company": "Updated Electronics",
        }
    )

    repository.save(updated)

    jobs = repository.list_jobs()

    assert len(jobs) == 1
    assert jobs[0].source_job_id == "JOB-001"
    assert jobs[0].title == "Senior Embedded Hardware Engineer"
    assert jobs[0].company == "Updated Electronics"

    session.close()
