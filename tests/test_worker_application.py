from datetime import datetime, timezone
from pathlib import Path

from pydantic import HttpUrl

from apps.worker.main import process_source
from packages.application.adapters.dry_run import DryRunApplicationAdapter
from packages.application.application_service import ApplicationService
from packages.application.discovery.target_discovery import ApplyTargetDiscovery
from packages.application.models import (
    ApplicationMethod,
    ApplicationRequest,
    ApplicationResult,
    ApplicationStatus,
)
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

        _, record = max(matches, key=lambda item: item[0])
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
        application_repository=application_repository,
        target_discovery=ApplyTargetDiscovery(),
    )

    assert result == (1, 1, 0)
    assert len(application_repository.records) == 1

    record = application_repository.records[1]

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
        application_repository=application_repository,
        target_discovery=ApplyTargetDiscovery(),
    )

    assert result == (1, 1, 0)
    assert len(application_repository.records) == 1

    record = application_repository.records[1]

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
        application_repository=application_repository,
        target_discovery=ApplyTargetDiscovery(),
    )

    assert result == (1, 1, 0)
    assert application_repository.records == {}


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


def test_worker_does_not_apply_alert_decision() -> None:
    job = make_job(
        source_job_id="ALERT-001",
        title="Senior OpenBMC Firmware Engineer",
        description="OpenBMC and embedded firmware development.",
    )

    job_repository = InMemoryJobRepository()
    decision_repository = InMemoryDecisionRepository()
    application_repository = FakeApplicationRepository()

    result = process_source(
        source=SingleJobSource(job),
        repository=job_repository,
        decision_repository=decision_repository,
        application_service=make_application_service(application_repository),
        application_repository=application_repository,
        target_discovery=ApplyTargetDiscovery(),
    )

    assert result == (1, 1, 0)
    assert application_repository.records == {}


class RecordingApplicationService(ApplicationService):
    """Application service that records whether execution was requested."""

    def __init__(self, repository: ApplicationRepository) -> None:
        adapter = DryRunApplicationAdapter()

        super().__init__(
            email_adapter=adapter,
            browser_adapter=adapter,
            repository=repository,
        )

        self.submit_calls = 0

    def submit(
        self,
        request: ApplicationRequest,
        job_id: int | None = None,
    ) -> ApplicationResult:
        self.submit_calls += 1
        return super().submit(request, job_id=job_id)


def test_execution_policy_blocks_already_submitted_application() -> None:
    job = make_job(
        source_job_id="ALREADY-SUBMITTED-001",
        source_url="https://example.com/careers/hardware-design-engineer/apply",
    )

    job_repository = InMemoryJobRepository()
    decision_repository = InMemoryDecisionRepository()
    application_repository = FakeApplicationRepository()

    application_repository.save(
        ApplicationRecord(
            job_id=1,
            method=ApplicationMethod.BROWSER,
            status=ApplicationStatus.SUBMITTED,
            apply_url=str(job.source_url),
        )
    )

    application_service = RecordingApplicationService(application_repository)

    result = process_source(
        source=SingleJobSource(job),
        repository=job_repository,
        decision_repository=decision_repository,
        application_service=application_service,
        application_repository=application_repository,
        target_discovery=ApplyTargetDiscovery(),
    )

    assert result == (1, 1, 0)
    assert application_service.submit_calls == 0


def test_execution_policy_blocks_active_application_attempt() -> None:
    job = make_job(
        source_job_id="ACTIVE-ATTEMPT-001",
        source_url="https://example.com/careers/hardware-design-engineer/apply",
    )

    job_repository = InMemoryJobRepository()
    decision_repository = InMemoryDecisionRepository()
    application_repository = FakeApplicationRepository()

    application_repository.save(
        ApplicationRecord(
            job_id=1,
            method=ApplicationMethod.BROWSER,
            status=ApplicationStatus.PENDING,
            apply_url=str(job.source_url),
        )
    )

    application_service = RecordingApplicationService(application_repository)

    result = process_source(
        source=SingleJobSource(job),
        repository=job_repository,
        decision_repository=decision_repository,
        application_service=application_service,
        application_repository=application_repository,
        target_discovery=ApplyTargetDiscovery(),
    )

    assert result == (1, 1, 0)
    assert application_service.submit_calls == 0





def test_worker_executes_browser_application_end_to_end() -> None:
    import functools
    import threading
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from packages.application.adapters.browser import BrowserApplicationAdapter
    from packages.application.application_service import ApplicationService
    from packages.application.profile import CandidateProfile
    from packages.persistence.models import Base
    from packages.persistence.sqlalchemy_application_repository import (
        SQLAlchemyApplicationRepository,
    )

    fixture_directory = Path(__file__).parent / "fixtures"
    resume_path = fixture_directory / "test_resume.pdf"

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    session = Session(engine)
    application_repository = SQLAlchemyApplicationRepository(session)

    handler = functools.partial(
        SimpleHTTPRequestHandler,
        directory=str(fixture_directory),
    )

    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )
    thread.start()

    try:
        application_url = (
            f"http://127.0.0.1:{server.server_port}/"
            "application/application_form.html"
        )

        job = make_job(
            source_job_id="BROWSER-E2E-001",
            source_url=application_url,
            description="Design hardware and PCB systems.",
        )

        job_repository = InMemoryJobRepository()
        decision_repository = InMemoryDecisionRepository()

        candidate = CandidateProfile(
            full_name="Harshraj Test",
            email="harshraj.test@example.com",
            phone="9876543210",
            location="Indore, India",
            resume_path=str(resume_path),
            linkedin_url=None,
            github_url=None,
            portfolio_url="https://example.com",
            education=[],
            skills=[],
            projects=[],
            application_answers={
                "experience_level": "fresher",
            },
        )

        browser_adapter = BrowserApplicationAdapter(
            candidate=candidate,
            headless=True,
        )

        application_service = ApplicationService(
            email_adapter=browser_adapter,
            browser_adapter=browser_adapter,
            repository=application_repository,
        )

        result = process_source(
            source=SingleJobSource(job),
            repository=job_repository,
            decision_repository=decision_repository,
            application_service=application_service,
            application_repository=application_repository,
            target_discovery=ApplyTargetDiscovery(),
        )

        assert result == (1, 1, 0)

        job_id = job_repository.get_id_by_source_job_id(
            source="test",
            source_job_id="BROWSER-E2E-001",
        )
        assert job_id is not None

        application = application_repository.get_latest(job_id)
        assert application is not None
        assert application.status == ApplicationStatus.SUBMITTED
        assert application.method == ApplicationMethod.BROWSER
        assert application.submitted_at is not None
        assert application.external_reference is not None
        assert "/application_success.html" in application.external_reference

    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
        session.close()
