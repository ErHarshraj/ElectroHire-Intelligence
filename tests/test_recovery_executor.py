from datetime import datetime, timezone

from packages.application.adapters.base import ApplicationAdapter
from packages.application.application_service import ApplicationService
from packages.application.discovery.target_discovery import ApplyTargetDiscovery
from packages.application.models import (
    ApplicationMethod,
    ApplicationRequest,
    ApplicationResult,
    ApplicationStatus,
)
from packages.application.recovery import (
    ApplicationRecoveryService,
    ApplicationRetryCandidate,
)
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


class RecordingAdapter(ApplicationAdapter):
    def __init__(self, result: ApplicationResult | None = None) -> None:
        self.requests: list[ApplicationRequest] = []
        self.result = result or ApplicationResult(
            status=ApplicationStatus.SUBMITTED,
            method=ApplicationMethod.EMAIL,
            message="application submitted successfully",
            external_reference="external-123",
        )

    def submit(self, request: ApplicationRequest) -> ApplicationResult:
        self.requests.append(request)
        return self.result


class FailingAdapter(ApplicationAdapter):
    def submit(self, request: ApplicationRequest) -> ApplicationResult:
        raise RuntimeError("adapter failure")


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
    application_service: ApplicationService | None = None,
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
        application_service=application_service,
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


def make_retry_candidate(
    application_repository: FakeApplicationRepository,
) -> "ApplicationRetryCandidate":
    from packages.application.recovery import ApplicationRetryCandidate

    application_id = application_repository.get_latest(1)
    assert application_id is not None
    assert application_id.id is not None

    return ApplicationRetryCandidate(
        job_id=1,
        application_id=application_id.id,
        method=application_id.method.value,
        message="failed application attempt is eligible for retry",
    )


def test_execute_submits_retry_through_application_service() -> None:
    adapter = RecordingAdapter()
    executor, _, application_repository = make_executor(make_job())

    application_repository.save(make_failed_application(job_id=1))
    candidate = make_retry_candidate(application_repository)

    # Bind the executor to the same repository used by the test after construction.
    executor.application_service = ApplicationService(
        email_adapter=adapter,
        browser_adapter=adapter,
        repository=application_repository,
    )

    plan, result = executor.execute(candidate)

    assert plan.action == RecoveryExecutionAction.READY
    assert result is not None
    assert result.status == ApplicationStatus.SUBMITTED
    assert len(adapter.requests) == 1
    request = adapter.requests[0]
    assert request.application_method == ApplicationMethod.EMAIL
    assert request.recruiter_email == "careers@example.com"
    assert request.source == "adzuna"
    assert request.source_job_id == "job-1"
    assert request.job_title == "Hardware Design Engineer"
    assert request.company == "Example Electronics"

    latest = application_repository.get_latest(1)
    assert latest is not None
    assert latest.status == ApplicationStatus.SUBMITTED


def test_execute_uses_current_target_when_retry_target_changed() -> None:
    adapter = RecordingAdapter()
    executor, _, application_repository = make_executor(make_job(
        description="Apply by email to new-careers@example.com"
    ))
    executor.application_service = ApplicationService(
        email_adapter=adapter,
        browser_adapter=adapter,
        repository=application_repository,
    )

    application_repository.save(make_failed_application(job_id=1))
    candidate = make_retry_candidate(application_repository)

    _, result = executor.execute(candidate)

    assert result is not None
    assert adapter.requests[0].recruiter_email == "new-careers@example.com"


def test_execute_skips_without_calling_adapter_when_target_disappeared() -> None:
    adapter = RecordingAdapter()
    executor, _, application_repository = make_executor(
        make_job(description="No application contact available")
    )
    executor.application_service = ApplicationService(
        email_adapter=adapter,
        browser_adapter=adapter,
        repository=application_repository,
    )

    application_repository.save(make_failed_application(job_id=1))
    candidate = make_retry_candidate(application_repository)

    plan, result = executor.execute(candidate)

    assert plan.action == RecoveryExecutionAction.SKIP
    assert result is None
    assert adapter.requests == []


def test_execute_skips_stale_candidate_without_calling_adapter() -> None:
    adapter = RecordingAdapter()
    executor, _, application_repository = make_executor(make_job())
    executor.application_service = ApplicationService(
        email_adapter=adapter,
        browser_adapter=adapter,
        repository=application_repository,
    )

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

    plan, result = executor.execute(candidate)

    assert plan.action == RecoveryExecutionAction.SKIP
    assert result is None
    assert adapter.requests == []


def test_execute_persists_paused_when_adapter_interrupted() -> None:
    executor, _, application_repository = make_executor(make_job())
    executor.application_service = ApplicationService(
        email_adapter=FailingAdapter(),
        browser_adapter=FailingAdapter(),
        repository=application_repository,
    )

    application_repository.save(make_failed_application(job_id=1))
    candidate = make_retry_candidate(application_repository)

    _, result = executor.execute(candidate)

    assert result is not None
    assert result.status == ApplicationStatus.PAUSED
    latest = application_repository.get_latest(1)
    assert latest is not None
    assert latest.status == ApplicationStatus.PAUSED


def test_execute_does_not_resubmit_if_job_became_submitted() -> None:
    adapter = RecordingAdapter()
    executor, _, application_repository = make_executor(make_job())
    executor.application_service = ApplicationService(
        email_adapter=adapter,
        browser_adapter=adapter,
        repository=application_repository,
    )

    application_repository.save(make_failed_application(job_id=1))
    candidate = make_retry_candidate(application_repository)
    application_repository.save(
        ApplicationRecord(
            job_id=1,
            method=ApplicationMethod.EMAIL,
            status=ApplicationStatus.SUBMITTED,
            started_at=datetime.now(timezone.utc),
            submitted_at=datetime.now(timezone.utc),
        )
    )

    plan, result = executor.execute(candidate)

    assert plan.action == RecoveryExecutionAction.SKIP
    assert result is None
    assert adapter.requests == []
