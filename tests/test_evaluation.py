from datetime import datetime, timezone

from pydantic import HttpUrl

from packages.domain.job import Job
from packages.domain.job_status import JobStatus
from packages.domain.lifecycle import JobLifecycle
from packages.matching.evaluation import JobEvaluationService
from packages.matching.relevance import JobRelevanceEngine
from packages.persistence.in_memory import InMemoryJobRepository


def create_job(
    title: str,
    description: str = "",
) -> Job:
    return Job(
        title=title,
        company="Test Company",
        description=description,
        source="test",
        source_job_id=title,
        source_url=HttpUrl("https://example.com/job/1"),
        discovered_at=datetime.now(timezone.utc),
    )


def create_service() -> tuple[JobEvaluationService, InMemoryJobRepository]:
    repository = InMemoryJobRepository()

    service = JobEvaluationService(
        relevance_engine=JobRelevanceEngine(),
        lifecycle=JobLifecycle(),
        repository=repository,
    )

    return service, repository


def test_relevant_job_becomes_evaluated() -> None:
    service, repository = create_service()
    job = create_job("Hardware Design Engineer")

    result = service.evaluate(job)

    assert result.is_relevant is True
    assert job.status == JobStatus.EVALUATED
    assert repository.list_jobs()[0].status == JobStatus.EVALUATED


def test_irrelevant_job_becomes_ignored() -> None:
    service, repository = create_service()
    job = create_job("Account Manager")

    result = service.evaluate(job)

    assert result.is_relevant is False
    assert job.status == JobStatus.IGNORED
    assert repository.list_jobs()[0].status == JobStatus.IGNORED


def test_evaluated_job_cannot_be_evaluated_again() -> None:
    service, _ = create_service()
    job = create_job("Hardware Design Engineer")

    service.evaluate(job)

    try:
        service.evaluate(job)
    except ValueError as exc:
        assert "Only discovered jobs can be evaluated" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_ignored_job_cannot_be_evaluated_again() -> None:
    service, _ = create_service()
    job = create_job("Account Manager")

    service.evaluate(job)

    try:
        service.evaluate(job)
    except ValueError as exc:
        assert "Only discovered jobs can be evaluated" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
