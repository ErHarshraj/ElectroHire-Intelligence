from datetime import datetime, timezone

from pydantic import HttpUrl

from apps.worker.main import process_source
from packages.application.adapters.dry_run import DryRunApplicationAdapter
from packages.application.application_service import ApplicationService
from packages.application.discovery.target_discovery import ApplyTargetDiscovery
from packages.application.models import ApplicationStatus
from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.persistence.application_repository import (
    ApplicationRecord,
    ApplicationRepository,
)
from packages.persistence.in_memory import InMemoryJobRepository
from packages.persistence.in_memory_decision import InMemoryDecisionRepository


class FakeApplicationRepository(ApplicationRepository):
    """In-memory application repository for worker integration tests."""

    def __init__(self) -> None:
        self.records: list[ApplicationRecord] = []

    def save(self, record: ApplicationRecord) -> None:
        self.records.append(record)

    def has_submitted_application(self, job_id: int) -> bool:
        return any(
            record.job_id == job_id
            and record.status == ApplicationStatus.SUBMITTED
            for record in self.records
        )


class SingleJobSource(JobSource):
    """Deterministic source returning one supplied job."""

    name = "test"

    def __init__(self, job: Job) -> None:
        self.job = job

    def fetch_jobs(self) -> list[Job]:
        return [self.job]


def make_job(
    *,
    source_job_id: str,
    title: str = "Hardware Design Engineer",
    source_url: str = "https://example.com/jobs/test",
    description: str = "Design hardware and PCB systems.",
) -> Job:
    timestamp = datetime(2026, 8, 28, tzinfo=timezone.utc)

    return Job(
        title=title,
        company="Test Electronics",
        location="Bengaluru, India",
        description=description,
        source="test",
        source_job_id=source_job_id,
        source_url=HttpUrl(source_url),
        employment_type="Full-time",
        experience_required="0-2 years",
        skills=["PCB Design", "Embedded C"],
        posted_at=timestamp,
        discovered_at=timestamp,
    )


def make_application_service(
    repository: ApplicationRepository,
) -> ApplicationService:
    adapter = DryRunApplicationAdapter()

    return ApplicationService(
        email_adapter=adapter,
        browser_adapter=adapter,
        repository=repository,
    )


def test_worker_prepares_browser_application() -> None:
    job = make_job(
        source_job_id="BROWSER-001",
        source_url="https://example.com/careers/hardware-design-engineer/apply",
    )

    job_repository = InMemoryJobRepository()
    decision_repository = InMemoryDecisionRepository()
    application_repository = FakeApplicationRepository()

    result = process_source(
        source=SingleJobSource(job),
        repository=job_repository,
        decision_repository=decision_repository,
        application_service=make_application_service(application_repository),
        target_discovery=ApplyTargetDiscovery(),
    )

    assert result == (1, 1, 0)
    assert len(application_repository.records) == 1

    record = application_repository.records[0]

    assert record.job_id == 1
    assert record.status == ApplicationStatus.PENDING
    assert record.apply_url == str(job.source_url)
    assert record.recruiter_email is None


def test_worker_prepares_email_application() -> None:
    job = make_job(
        source_job_id="EMAIL-001",
        description=(
            "Design hardware and PCB systems. "
            "Contact recruiter@example.com for applications."
        ),
    )

    job_repository = InMemoryJobRepository()
    decision_repository = InMemoryDecisionRepository()
    application_repository = FakeApplicationRepository()

    result = process_source(
        source=SingleJobSource(job),
        repository=job_repository,
        decision_repository=decision_repository,
        application_service=make_application_service(application_repository),
        target_discovery=ApplyTargetDiscovery(),
    )

    assert result == (1, 1, 0)
    assert len(application_repository.records) == 1

    record = application_repository.records[0]

    assert record.job_id == 1
    assert record.status == ApplicationStatus.PENDING
    assert record.apply_url is None
    assert record.recruiter_email == "recruiter@example.com"


def test_worker_does_not_create_application_without_target() -> None:
    job = make_job(
        source_job_id="NO-TARGET-001",
    )

    job_repository = InMemoryJobRepository()
    decision_repository = InMemoryDecisionRepository()
    application_repository = FakeApplicationRepository()

    result = process_source(
        source=SingleJobSource(job),
        repository=job_repository,
        decision_repository=decision_repository,
        application_service=make_application_service(application_repository),
        target_discovery=ApplyTargetDiscovery(),
    )

    assert result == (1, 1, 0)
    assert application_repository.records == []


def test_worker_does_not_create_application_when_application_infrastructure_is_disabled() -> None:
    job = make_job(
        source_job_id="DISABLED-001",
    )

    job_repository = InMemoryJobRepository()
    decision_repository = InMemoryDecisionRepository()

    result = process_source(
        source=SingleJobSource(job),
        repository=job_repository,
        decision_repository=decision_repository,
    )

    assert result == (1, 1, 0)
