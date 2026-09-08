from packages.application.adapters.dry_run import DryRunApplicationAdapter
from packages.application.application_service import ApplicationService
from packages.application.models import (
    ApplicationMethod,
    ApplicationRequest,
    ApplicationStatus,
)
from packages.persistence.application_repository import (
    ApplicationRecord,
    ApplicationRepository,
)


class FakeApplicationRepository(ApplicationRepository):
    """In-memory repository for application-service tests."""

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


def make_service(
    repository: ApplicationRepository | None = None,
) -> ApplicationService:
    adapter = DryRunApplicationAdapter()

    return ApplicationService(
        email_adapter=adapter,
        browser_adapter=adapter,
        repository=repository,
    )


def test_browser_application_requires_apply_url() -> None:
    request = ApplicationRequest(
        source="adzuna",
        source_job_id="123",
        job_title="Hardware Design Engineer",
        company="Test Electronics",
        application_method=ApplicationMethod.BROWSER,
    )

    result = make_service().submit(request)

    assert result.status == ApplicationStatus.FAILED
    assert "apply URL" in result.message


def test_email_application_requires_recruiter_email() -> None:
    request = ApplicationRequest(
        source="adzuna",
        source_job_id="123",
        job_title="Hardware Design Engineer",
        company="Test Electronics",
        application_method=ApplicationMethod.EMAIL,
    )

    result = make_service().submit(request)

    assert result.status == ApplicationStatus.FAILED
    assert "recruiter email" in result.message


def test_browser_application_is_validated() -> None:
    request = ApplicationRequest(
        source="adzuna",
        source_job_id="123",
        job_title="Hardware Design Engineer",
        company="Test Electronics",
        application_method=ApplicationMethod.BROWSER,
        apply_url="https://example.com/apply",
    )

    result = make_service().submit(request)

    assert result.status == ApplicationStatus.PENDING
    assert result.method == ApplicationMethod.BROWSER


def test_email_application_is_validated() -> None:
    request = ApplicationRequest(
        source="adzuna",
        source_job_id="123",
        job_title="Hardware Design Engineer",
        company="Test Electronics",
        application_method=ApplicationMethod.EMAIL,
        recruiter_email="recruiter@example.com",
    )

    result = make_service().submit(request)

    assert result.status == ApplicationStatus.PENDING
    assert result.method == ApplicationMethod.EMAIL


def test_application_result_is_persisted() -> None:
    repository = FakeApplicationRepository()

    request = ApplicationRequest(
        source="adzuna",
        source_job_id="123",
        job_title="Hardware Design Engineer",
        company="Test Electronics",
        application_method=ApplicationMethod.BROWSER,
        apply_url="https://example.com/apply",
    )

    result = make_service(repository).submit(request, job_id=42)

    assert result.status == ApplicationStatus.PENDING
    assert len(repository.records) == 1
    assert repository.records[0].job_id == 42
    assert repository.records[0].apply_url == "https://example.com/apply"


def test_duplicate_application_is_not_submitted() -> None:
    repository = FakeApplicationRepository()

    repository.save(
        ApplicationRecord(
            job_id=42,
            method=ApplicationMethod.BROWSER,
            status=ApplicationStatus.SUBMITTED,
            apply_url="https://example.com/apply",
        )
    )

    request = ApplicationRequest(
        source="adzuna",
        source_job_id="123",
        job_title="Hardware Design Engineer",
        company="Test Electronics",
        application_method=ApplicationMethod.BROWSER,
        apply_url="https://example.com/apply",
    )

    result = make_service(repository).submit(request, job_id=42)

    assert result.status == ApplicationStatus.ALREADY_SUBMITTED
    assert result.method == ApplicationMethod.BROWSER
    assert len(repository.records) == 1
