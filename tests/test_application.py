from datetime import datetime, timezone

import pytest

from packages.application.adapters.base import ApplicationAdapter
from packages.application.adapters.dry_run import DryRunApplicationAdapter
from packages.application.application_service import ApplicationService
from packages.application.career_application_service import (
    CareerApplicationService,
)
from packages.application.career_models import (
    CareerApplicationRecord,
    CareerApplicationStatus,
)
from packages.application.models import (
    ApplicationMethod,
    ApplicationRequest,
    ApplicationResult,
    ApplicationStatus,
)
from packages.persistence.application_repository import (
    ApplicationRecord,
    ApplicationRepository,
)
from packages.persistence.career_application_repository import (
    CareerApplicationRepository,
)


class FakeApplicationRepository(ApplicationRepository):
    """In-memory repository for application-service tests."""

    def __init__(self) -> None:
        self.records: dict[int, ApplicationRecord] = {}
        self.next_id = 1

    def save(self, record: ApplicationRecord) -> int:
        application_id = self.next_id
        self.next_id += 1

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
            (application_id, record)
            for application_id, record in self.records.items()
            if record.job_id == job_id
        ]

        if not matches:
            return None

        application_id, record = max(matches, key=lambda item: item[0])

        return record


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
            id=application_id,
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


class FakeCareerApplicationRepository(CareerApplicationRepository):
    """In-memory repository for career-application synchronization tests."""

    def __init__(self) -> None:
        self.records: dict[int, CareerApplicationRecord] = {}
        self.next_id = 1

    def save(self, record: CareerApplicationRecord) -> int:
        application_id = self.next_id
        self.next_id += 1

        self.records[application_id] = CareerApplicationRecord(
            job_id=record.job_id,
            status=record.status,
            id=application_id,
            application_url=record.application_url,
            applied_at=record.applied_at,
            notes=record.notes,
            last_followup_at=record.last_followup_at,
            next_followup_at=record.next_followup_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

        return application_id

    def get(self, application_id: int) -> CareerApplicationRecord | None:
        return self.records.get(application_id)

    def get_by_job(
        self,
        job_id: int,
    ) -> CareerApplicationRecord | None:
        for record in self.records.values():
            if record.job_id == job_id:
                return record
        return None

    def list_by_status(
        self,
        status: CareerApplicationStatus,
    ) -> list[CareerApplicationRecord]:
        return [
            record
            for record in self.records.values()
            if record.status == status
        ]

    def update(
        self,
        application_id: int,
        *,
        status: CareerApplicationStatus,
        application_url: str | None = None,
        applied_at: datetime | None = None,
        notes: str = "",
        last_followup_at: datetime | None = None,
        next_followup_at: datetime | None = None,
    ) -> None:
        record = self.records[application_id]

        self.records[application_id] = CareerApplicationRecord(
            job_id=record.job_id,
            status=status,
            id=application_id,
            application_url=application_url,
            applied_at=applied_at,
            notes=notes,
            last_followup_at=last_followup_at,
            next_followup_at=next_followup_at,
            created_at=record.created_at,
            updated_at=datetime.now(timezone.utc),
        )


class SuccessfulAdapter(ApplicationAdapter):
    """Adapter that simulates a successful real submission."""

    def submit(self, request: ApplicationRequest) -> ApplicationResult:
        return ApplicationResult(
            status=ApplicationStatus.SUBMITTED,
            method=request.application_method,
            message="application submitted successfully",
            external_reference="external-123",
        )


class FailingAdapter(ApplicationAdapter):
    """Adapter that simulates an interrupted submission."""

    def submit(self, request: ApplicationRequest) -> ApplicationResult:
        raise RuntimeError("simulated adapter failure")


def make_request(
    method: ApplicationMethod = ApplicationMethod.BROWSER,
) -> ApplicationRequest:
    return ApplicationRequest(
        source="adzuna",
        source_job_id="job-123",
        job_title="Hardware Engineer",
        company="Example Corp",
        application_method=method,
        apply_url="https://example.com/careers/apply",
        recruiter_email="careers@example.com",
        submission_authorized=True,
    )


def make_service(
    repository: ApplicationRepository | None = None,
    adapter: ApplicationAdapter | None = None,
    career_application_service: CareerApplicationService | None = None,
) -> ApplicationService:
    adapter = adapter or DryRunApplicationAdapter()

    return ApplicationService(
        email_adapter=adapter,
        browser_adapter=adapter,
        repository=repository,
        career_application_service=career_application_service,
    )


def seed_application(
    repository: FakeApplicationRepository,
    *,
    job_id: int,
    status: ApplicationStatus,
) -> int:
    return repository.save(
        ApplicationRecord(
            job_id=job_id,
            method=ApplicationMethod.BROWSER,
            status=status,
            apply_url="https://example.com/careers/apply",
            message=f"seeded {status.value} application",
            started_at=datetime.now(timezone.utc),
        )
    )


def test_new_application_creates_persisted_attempt() -> None:
    repository = FakeApplicationRepository()
    service = make_service(repository)

    result = service.submit(make_request(), job_id=42)

    assert result.status == ApplicationStatus.PENDING
    assert len(repository.records) == 1

    record = repository.records[1]

    assert record.job_id == 42
    assert record.status == ApplicationStatus.PENDING
    assert record.method == ApplicationMethod.BROWSER
    assert record.apply_url == "https://example.com/careers/apply"
    assert record.started_at is not None


def test_successful_submission_is_persisted() -> None:
    repository = FakeApplicationRepository()
    service = make_service(
        repository,
        adapter=SuccessfulAdapter(),
    )

    result = service.submit(make_request(), job_id=42)

    assert result.status == ApplicationStatus.SUBMITTED
    assert result.external_reference == "external-123"

    record = repository.get_latest(42)

    assert record is not None
    assert record.status == ApplicationStatus.SUBMITTED
    assert record.external_reference == "external-123"
    assert record.message == "application submitted successfully"
    assert record.submitted_at is not None


def test_successful_submission_creates_career_application() -> None:
    repository = FakeApplicationRepository()
    career_repository = FakeCareerApplicationRepository()
    career_service = CareerApplicationService(career_repository)

    service = make_service(
        repository,
        adapter=SuccessfulAdapter(),
        career_application_service=career_service,
    )

    result = service.submit(make_request(), job_id=42)

    assert result.status == ApplicationStatus.SUBMITTED

    career_application = career_repository.get_by_job(42)

    assert career_application is not None
    assert career_application.status == CareerApplicationStatus.APPLIED
    assert career_application.applied_at is not None

    application_record = repository.get_latest(42)

    assert application_record is not None
    assert application_record.submitted_at is not None
    assert career_application.applied_at == application_record.submitted_at


def test_successful_submission_moves_shortlisted_to_applied() -> None:
    repository = FakeApplicationRepository()
    career_repository = FakeCareerApplicationRepository()
    career_service = CareerApplicationService(career_repository)

    career_application_id = career_service.create(
        job_id=42,
        status=CareerApplicationStatus.SHORTLISTED,
    )

    service = make_service(
        repository,
        adapter=SuccessfulAdapter(),
        career_application_service=career_service,
    )

    result = service.submit(make_request(), job_id=42)

    assert result.status == ApplicationStatus.SUBMITTED

    career_application = career_repository.get(career_application_id)

    assert career_application is not None
    assert career_application.status == CareerApplicationStatus.APPLIED
    assert career_application.applied_at is not None

    application_record = repository.get_latest(42)

    assert application_record is not None
    assert application_record.submitted_at is not None
    assert career_application.applied_at == application_record.submitted_at


def test_successful_submission_preserves_shortlisted_tracking_metadata() -> None:
    repository = FakeApplicationRepository()
    career_repository = FakeCareerApplicationRepository()
    career_service = CareerApplicationService(career_repository)

    career_application_id = career_service.create(
        job_id=42,
        status=CareerApplicationStatus.SHORTLISTED,
        application_url="https://example.com/apply",
        notes="Important hardware role",
    )

    service = make_service(
        repository,
        adapter=SuccessfulAdapter(),
        career_application_service=career_service,
    )

    result = service.submit(make_request(), job_id=42)

    assert result.status == ApplicationStatus.SUBMITTED

    career_application = career_repository.get(career_application_id)

    assert career_application is not None
    assert career_application.status == CareerApplicationStatus.APPLIED
    assert career_application.application_url == "https://example.com/apply"
    assert career_application.notes == "Important hardware role"
    assert career_application.applied_at is not None


def test_successful_submission_preserves_existing_applied_status() -> None:
    repository = FakeApplicationRepository()
    career_repository = FakeCareerApplicationRepository()
    career_service = CareerApplicationService(career_repository)

    career_application_id = career_service.create(
        job_id=42,
        status=CareerApplicationStatus.APPLIED,
    )

    service = make_service(
        repository,
        adapter=SuccessfulAdapter(),
        career_application_service=career_service,
    )

    result = service.submit(make_request(), job_id=42)

    assert result.status == ApplicationStatus.SUBMITTED

    career_application = career_repository.get(career_application_id)

    assert career_application is not None
    assert career_application.status == CareerApplicationStatus.APPLIED


def test_failed_submission_does_not_create_career_application() -> None:
    repository = FakeApplicationRepository()
    career_repository = FakeCareerApplicationRepository()
    career_service = CareerApplicationService(career_repository)

    service = make_service(
        repository,
        adapter=FailingAdapter(),
        career_application_service=career_service,
    )

    result = service.submit(make_request(), job_id=42)

    assert result.status == ApplicationStatus.PAUSED
    assert career_repository.get_by_job(42) is None


def test_submission_without_career_service_preserves_existing_behavior() -> None:
    repository = FakeApplicationRepository()

    service = make_service(
        repository,
        adapter=SuccessfulAdapter(),
    )

    result = service.submit(make_request(), job_id=42)

    assert result.status == ApplicationStatus.SUBMITTED
    assert len(repository.records) == 1


def test_adapter_exception_moves_application_to_paused() -> None:
    repository = FakeApplicationRepository()
    service = make_service(
        repository,
        adapter=FailingAdapter(),
    )

    result = service.submit(make_request(), job_id=42)

    assert result.status == ApplicationStatus.PAUSED
    assert "manual recovery" in result.message

    record = repository.get_latest(42)

    assert record is not None
    assert record.status == ApplicationStatus.PAUSED
    assert "simulated adapter failure" in record.message


def test_existing_submitted_application_is_not_submitted_again() -> None:
    repository = FakeApplicationRepository()
    seed_application(
        repository,
        job_id=42,
        status=ApplicationStatus.SUBMITTED,
    )

    service = make_service(
        repository,
        adapter=SuccessfulAdapter(),
    )

    result = service.submit(make_request(), job_id=42)

    assert result.status == ApplicationStatus.ALREADY_SUBMITTED
    assert len(repository.records) == 1


@pytest.mark.parametrize(
    "status",
    [
        ApplicationStatus.PENDING,
        ApplicationStatus.IN_PROGRESS,
        ApplicationStatus.PAUSED,
    ],
)
def test_active_application_attempt_blocks_new_submission(
    status: ApplicationStatus,
) -> None:
    repository = FakeApplicationRepository()
    seed_application(
        repository,
        job_id=42,
        status=status,
    )

    service = make_service(
        repository,
        adapter=SuccessfulAdapter(),
    )

    result = service.submit(make_request(), job_id=42)

    assert result.status == ApplicationStatus.PAUSED
    assert "manual recovery" in result.message
    assert len(repository.records) == 1


def test_failed_application_allows_retry() -> None:
    repository = FakeApplicationRepository()
    seed_application(
        repository,
        job_id=42,
        status=ApplicationStatus.FAILED,
    )

    service = make_service(
        repository,
        adapter=SuccessfulAdapter(),
    )

    result = service.submit(make_request(), job_id=42)

    assert result.status == ApplicationStatus.SUBMITTED
    assert len(repository.records) == 2

    latest = repository.get_latest(42)

    assert latest is not None
    assert latest.status == ApplicationStatus.SUBMITTED


def test_application_history_is_retained() -> None:
    repository = FakeApplicationRepository()

    first_id = seed_application(
        repository,
        job_id=42,
        status=ApplicationStatus.FAILED,
    )

    second_id = seed_application(
        repository,
        job_id=42,
        status=ApplicationStatus.PAUSED,
    )

    assert first_id != second_id
    assert len(repository.records) == 2

    assert repository.records[first_id].status == ApplicationStatus.FAILED
    assert repository.records[second_id].status == ApplicationStatus.PAUSED


def test_application_without_persistence_uses_adapter() -> None:
    service = make_service(
        adapter=SuccessfulAdapter(),
    )

    result = service.submit(make_request())

    assert result.status == ApplicationStatus.SUBMITTED


def test_email_application_requires_recruiter_email() -> None:
    service = make_service()

    request = ApplicationRequest(
        source="adzuna",
        source_job_id="job-123",
        job_title="Hardware Engineer",
        company="Example Corp",
        application_method=ApplicationMethod.EMAIL,
        recruiter_email=None,
    )

    result = service.submit(request)

    assert result.status == ApplicationStatus.FAILED
    assert "recruiter email" in result.message


def test_browser_application_requires_apply_url() -> None:
    service = make_service()

    request = ApplicationRequest(
        source="adzuna",
        source_job_id="job-123",
        job_title="Hardware Engineer",
        company="Example Corp",
        application_method=ApplicationMethod.BROWSER,
        apply_url=None,
    )

    result = service.submit(request)

    assert result.status == ApplicationStatus.FAILED
    assert "apply URL" in result.message


def test_successful_submission_preserves_screening_status() -> None:
    repository = FakeApplicationRepository()
    career_repository = FakeCareerApplicationRepository()
    career_service = CareerApplicationService(career_repository)

    career_application_id = career_service.create(
        job_id=42,
        status=CareerApplicationStatus.SHORTLISTED,
    )

    career_service.transition(
        career_application_id,
        CareerApplicationStatus.APPLIED,
    )

    career_service.transition(
        career_application_id,
        CareerApplicationStatus.SCREENING,
    )

    service = make_service(
        repository,
        adapter=SuccessfulAdapter(),
        career_application_service=career_service,
    )

    result = service.submit(make_request(), job_id=42)

    assert result.status == ApplicationStatus.SUBMITTED

    career_application = career_repository.get(career_application_id)

    assert career_application is not None
    assert career_application.status == CareerApplicationStatus.SCREENING
