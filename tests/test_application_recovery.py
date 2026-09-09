from datetime import datetime, timezone

from packages.application.models import ApplicationMethod, ApplicationStatus
from packages.application.recovery import (
    ApplicationRecoveryService,
    RecoveryAction,
)
from packages.persistence.application_repository import (
    ApplicationRecord,
    ApplicationRepository,
)


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


def make_record(
    status: ApplicationStatus,
    job_id: int = 42,
) -> ApplicationRecord:
    return ApplicationRecord(
        job_id=job_id,
        method=ApplicationMethod.EMAIL,
        status=status,
        started_at=datetime.now(timezone.utc),
    )


def test_no_previous_attempt_requires_no_recovery() -> None:
    repository = FakeApplicationRepository()
    service = ApplicationRecoveryService(repository)

    report = service.inspect(42)

    assert report.job_id == 42
    assert report.status is None
    assert report.action == RecoveryAction.NONE


def test_pending_attempt_requires_inspection() -> None:
    repository = FakeApplicationRepository()
    application_id = repository.save(
        make_record(ApplicationStatus.PENDING)
    )
    service = ApplicationRecoveryService(repository)

    report = service.inspect(42)

    assert report.status == ApplicationStatus.PENDING
    assert report.action == RecoveryAction.INSPECT
    assert report.application_id == application_id


def test_in_progress_attempt_is_not_automatically_retried() -> None:
    repository = FakeApplicationRepository()
    repository.save(make_record(ApplicationStatus.IN_PROGRESS))
    service = ApplicationRecoveryService(repository)

    report = service.inspect(42)

    assert report.status == ApplicationStatus.IN_PROGRESS
    assert report.action == RecoveryAction.INSPECT
    assert "automatic retry" in report.message


def test_paused_attempt_requires_manual_recovery() -> None:
    repository = FakeApplicationRepository()
    repository.save(make_record(ApplicationStatus.PAUSED))
    service = ApplicationRecoveryService(repository)

    report = service.inspect(42)

    assert report.status == ApplicationStatus.PAUSED
    assert report.action == RecoveryAction.MANUAL_RECOVERY


def test_failed_attempt_is_retryable() -> None:
    repository = FakeApplicationRepository()
    repository.save(make_record(ApplicationStatus.FAILED))
    service = ApplicationRecoveryService(repository)

    report = service.inspect(42)

    assert report.status == ApplicationStatus.FAILED
    assert report.action == RecoveryAction.RETRY


def test_submitted_attempt_must_never_be_resubmitted() -> None:
    repository = FakeApplicationRepository()
    repository.save(make_record(ApplicationStatus.SUBMITTED))
    service = ApplicationRecoveryService(repository)

    report = service.inspect(42)

    assert report.status == ApplicationStatus.SUBMITTED
    assert report.action == RecoveryAction.DO_NOT_RESUBMIT


def test_already_submitted_attempt_must_never_be_resubmitted() -> None:
    repository = FakeApplicationRepository()
    repository.save(make_record(ApplicationStatus.ALREADY_SUBMITTED))
    service = ApplicationRecoveryService(repository)

    report = service.inspect(42)

    assert report.status == ApplicationStatus.ALREADY_SUBMITTED
    assert report.action == RecoveryAction.DO_NOT_RESUBMIT


def test_recovery_service_does_not_modify_repository() -> None:
    repository = FakeApplicationRepository()
    repository.save(make_record(ApplicationStatus.FAILED))
    before = dict(repository.records)

    service = ApplicationRecoveryService(repository)

    service.inspect(42)

    assert repository.records == before


def test_retry_plan_contains_failed_attempt() -> None:
    repository = FakeApplicationRepository()
    application_id = repository.save(
        make_record(ApplicationStatus.FAILED, job_id=100)
    )
    service = ApplicationRecoveryService(repository)

    plan = service.build_retry_plan()

    assert len(plan) == 1
    assert plan[0].job_id == 100
    assert plan[0].application_id == application_id
    assert plan[0].method == "email"


def test_retry_plan_excludes_submitted_job() -> None:
    repository = FakeApplicationRepository()
    repository.save(make_record(ApplicationStatus.FAILED, job_id=101))
    repository.save(make_record(ApplicationStatus.SUBMITTED, job_id=101))
    service = ApplicationRecoveryService(repository)

    plan = service.build_retry_plan()

    assert plan == []


def test_retry_plan_excludes_failed_attempt_when_newer_active_attempt_exists() -> None:
    repository = FakeApplicationRepository()

    repository.save(make_record(ApplicationStatus.FAILED, job_id=102))
    repository.save(make_record(ApplicationStatus.PENDING, job_id=102))

    service = ApplicationRecoveryService(repository)

    plan = service.build_retry_plan()

    assert plan == []


def test_retry_plan_excludes_failed_attempt_when_newer_submitted_attempt_exists() -> None:
    repository = FakeApplicationRepository()

    repository.save(make_record(ApplicationStatus.FAILED, job_id=103))
    repository.save(make_record(ApplicationStatus.SUBMITTED, job_id=103))

    service = ApplicationRecoveryService(repository)

    plan = service.build_retry_plan()

    assert plan == []


def test_retry_plan_is_deterministic() -> None:
    repository = FakeApplicationRepository()

    repository.save(make_record(ApplicationStatus.FAILED, job_id=200))
    repository.save(make_record(ApplicationStatus.FAILED, job_id=201))
    repository.save(make_record(ApplicationStatus.FAILED, job_id=202))

    service = ApplicationRecoveryService(repository)

    first_plan = service.build_retry_plan()
    second_plan = service.build_retry_plan()

    assert first_plan == second_plan
    assert [candidate.job_id for candidate in first_plan] == [
        200,
        201,
        202,
    ]
