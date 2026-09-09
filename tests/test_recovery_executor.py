from datetime import datetime, timezone

from packages.application.discovery.target_discovery import ApplyTargetDiscovery
from packages.application.models import ApplicationMethod, ApplicationStatus
from packages.application.recovery import ApplicationRecoveryService
from packages.application.recovery_executor import (
    ApplicationRecoveryExecutor,
    RecoveryExecutionAction,
)
from packages.domain.job import Job
from packages.persistence.application_repository import (
    ApplicationRecord,
    ApplicationRepository,
)
from packages.persistence.job_repository import JobRepository


class FakeJobRepository(JobRepository):
    def __init__(self) -> None:
        self.jobs: list[Job] = []

    def save(self, job: Job) -> None:
        self.jobs.append(job)

    def get_by_source_job_id(
        self,
        source: str,
        source_job_id: str,
    ) -> Job | None:
        for job in self.jobs:
            if (
                job.source == source
                and job.source_job_id == source_job_id
            ):
                return job
        return None

    def get_id_by_source_job_id(
        self,
        source: str,
        source_job_id: str,
    ) -> int | None:
        for index, job in enumerate(self.jobs, start=1):
            if (
                job.source == source
                and job.source_job_id == source_job_id
            ):
                return index
        return None

    def list_jobs(self) -> list[Job]:
        return self.jobs


class FakeApplicationRepository(ApplicationRepository):
    def __init__(self) -> None:
        self.records: dict[int, ApplicationRecord] = {}

    def save(self, record: ApplicationRecord) -> int:
        application_id = len(self.records) + 1

        self.records[application_id] = ApplicationRecord(
            job_id=record.job_id,
            method=record.method,
            status=record.status,
            id=application_id,
            apply_url=record.apply_url,
            recruiter_email=record.recruiter_email,
            external_reference=record.external_reference,
            message=record.message,
            started_at=record.started_at,
            submitted_at=record.submitted_at,
        )

        return application_id

    def get_latest(self, job_id: int) -> ApplicationRecord | None:
        matches = [
            record
            for record in self.records.values()
            if record.job_id == job_id
        ]

        if not matches:
            return None

        return max(matches, key=lambda record: record.id or 0)

    def get_by_status(
        self,
        status: ApplicationStatus,
    ) -> list[ApplicationRecord]:
        return [
            record
            for record in self.records.values()
            if record.status == status
        ]

    def list_active_attempts(self) -> list[ApplicationRecord]:
        active_statuses = {
            ApplicationStatus.PENDING,
            ApplicationStatus.IN_PROGRESS,
            ApplicationStatus.PAUSED,
        }

        return [
            record
            for record in self.records.values()
            if record.status in active_statuses
        ]

    def list_retryable_attempts(self) -> list[ApplicationRecord]:
        return [
            record
            for record in self.records.values()
            if record.status == ApplicationStatus.FAILED
        ]

    def update(
        self,
        application_id: int,
        *,
        status: ApplicationStatus,
        message: str = "",
        external_reference: str | None = None,
        submitted_at: datetime | None = None,
    ) -> None:
        record = self.records[application_id]

        self.records[application_id] = ApplicationRecord(
            job_id=record.job_id,
            method=record.method,
            status=status,
            id=record.id,
            apply_url=record.apply_url,
            recruiter_email=record.recruiter_email,
            external_reference=external_reference,
            message=message,
            started_at=record.started_at,
            submitted_at=submitted_at,
        )

    def has_submitted_application(self, job_id: int) -> bool:
        return any(
            record.job_id == job_id
            and record.status == ApplicationStatus.SUBMITTED
            for record in self.records.values()
        )


def make_job(
    *,
    source_job_id: str = "job-1",
    description: str = "Apply by email to careers@example.com",
) -> Job:
    return Job(
        title="Hardware Design Engineer",
        company="Example Electronics",
        location="India",
        description=description,
        source="adzuna",
        source_job_id=source_job_id,
        source_url="https://example.com/jobs/job-1",
        discovered_at=datetime.now(timezone.utc),
    )


def make_failed_application(job_id: int) -> ApplicationRecord:
    return ApplicationRecord(
        job_id=job_id,
        method=ApplicationMethod.EMAIL,
        status=ApplicationStatus.FAILED,
        recruiter_email="old@example.com",
        started_at=datetime.now(timezone.utc),
    )


def make_executor(
    job: Job | None = None,
) -> tuple[
    ApplicationRecoveryExecutor,
    FakeJobRepository,
    FakeApplicationRepository,
]:
    job_repository = FakeJobRepository()

    if job is not None:
        job_repository.save(job)

    application_repository = FakeApplicationRepository()

    executor = ApplicationRecoveryExecutor(
        job_repository=job_repository,
        application_repository=application_repository,
        target_discovery=ApplyTargetDiscovery(),
    )

    return executor, job_repository, application_repository


def test_prepare_returns_ready_for_current_email_target() -> None:
    executor, _, application_repository = make_executor(make_job())

    application_id = application_repository.save(
        make_failed_application(job_id=1)
    )

    candidate = ApplicationRecoveryService(
        application_repository
    ).build_retry_plan()[0]

    assert candidate.application_id == application_id

    plan = executor.prepare(candidate)

    assert plan.action == RecoveryExecutionAction.READY
    assert plan.application_method == ApplicationMethod.EMAIL
    assert plan.recruiter_email == "careers@example.com"


def test_prepare_skips_missing_job() -> None:
    executor, _, application_repository = make_executor()

    application_repository.save(make_failed_application(job_id=99))

    candidate = ApplicationRecoveryService(
        application_repository
    ).build_retry_plan()[0]

    plan = executor.prepare(candidate)

    assert plan.action == RecoveryExecutionAction.SKIP
    assert plan.message == "job no longer exists"


def test_prepare_skips_when_target_disappeared() -> None:
    job = make_job(description="No application contact available")
    executor, _, application_repository = make_executor(job)

    application_repository.save(make_failed_application(job_id=1))

    candidate = ApplicationRecoveryService(
        application_repository
    ).build_retry_plan()[0]

    plan = executor.prepare(candidate)

    assert plan.action == RecoveryExecutionAction.SKIP
    assert "no current application target" in plan.message


def test_prepare_uses_current_target_instead_of_old_target() -> None:
    job = make_job(
        description="Send applications to new-careers@example.com"
    )

    executor, _, application_repository = make_executor(job)

    application_repository.save(
        ApplicationRecord(
            job_id=1,
            method=ApplicationMethod.EMAIL,
            status=ApplicationStatus.FAILED,
            recruiter_email="old@example.com",
            started_at=datetime.now(timezone.utc),
        )
    )

    candidate = ApplicationRecoveryService(
        application_repository
    ).build_retry_plan()[0]

    plan = executor.prepare(candidate)

    assert plan.action == RecoveryExecutionAction.READY
    assert plan.recruiter_email == "new-careers@example.com"


def test_prepare_skips_if_newer_attempt_exists() -> None:
    executor, _, application_repository = make_executor(make_job())

    application_repository.save(make_failed_application(job_id=1))

    application_repository.save(
        ApplicationRecord(
            job_id=1,
            method=ApplicationMethod.EMAIL,
            status=ApplicationStatus.PAUSED,
            started_at=datetime.now(timezone.utc),
        )
    )

    from packages.application.recovery import ApplicationRetryCandidate

    candidate = ApplicationRetryCandidate(
        job_id=1,
        application_id=1,
        method="email",
        message="failed application attempt is eligible for retry",
    )

    plan = executor.prepare(candidate)

    assert plan.action == RecoveryExecutionAction.SKIP
    assert "no longer the latest" in plan.message


def test_prepare_skips_already_submitted_job() -> None:
    executor, _, application_repository = make_executor(make_job())

    application_repository.save(make_failed_application(job_id=1))

    application_repository.save(
        ApplicationRecord(
            job_id=1,
            method=ApplicationMethod.EMAIL,
            status=ApplicationStatus.SUBMITTED,
            started_at=datetime.now(timezone.utc),
            submitted_at=datetime.now(timezone.utc),
        )
    )

    candidate = ApplicationRecoveryService(
        application_repository
    ).build_retry_plan()

    assert candidate == []
