from datetime import datetime, timezone
from unittest.mock import Mock

from pydantic import HttpUrl

from apps.worker.cycle import WorkerCycle
from packages.application.application_service import ApplicationService
from packages.application.approval import ApplicationApprovalService
from packages.application.discovery.target_discovery import ApplyTargetDiscovery
from packages.application.models import (
    ApplicationApprovalRequest,
    ApplicationApprovalStatus,
    ApplicationMethod,
    ApplicationResult,
    ApplicationStatus,
)
from packages.common.config import Settings
from packages.domain.job import Job
from packages.matching.decision import DecisionAction
from packages.persistence.application_approval_repository import (
    ApplicationApprovalRecord,
    ApplicationApprovalRepository,
)
from packages.persistence.application_repository import ApplicationRepository
from packages.persistence.decision_repository import DecisionRepository
from packages.persistence.job_repository import JobRepository


class FakeApprovalRepository(ApplicationApprovalRepository):
    def __init__(self) -> None:
        self.records: dict[int, ApplicationApprovalRecord] = {}
        self.next_id = 1

    def save(self, record: ApplicationApprovalRecord) -> int:
        approval_id = self.next_id
        self.next_id += 1

        self.records[approval_id] = ApplicationApprovalRecord(
            job_id=record.job_id,
            source=record.source,
            source_job_id=record.source_job_id,
            job_title=record.job_title,
            company=record.company,
            method=record.method,
            status=record.status,
            id=approval_id,
            apply_url=record.apply_url,
            recruiter_email=record.recruiter_email,
            reason=record.reason,
            created_at=record.created_at,
            approved_at=record.approved_at,
            rejected_at=record.rejected_at,
            consumed_at=record.consumed_at,
        )

        return approval_id

    def get(self, approval_id: int) -> ApplicationApprovalRecord | None:
        return self.records.get(approval_id)

    def get_latest(self, job_id: int) -> ApplicationApprovalRecord | None:
        matches = [
            record
            for record in self.records.values()
            if record.job_id == job_id
        ]

        if not matches:
            return None

        return max(matches, key=lambda record: record.id or 0)

    def get_pending(self, job_id: int) -> ApplicationApprovalRecord | None:
        matches = [
            record
            for record in self.records.values()
            if record.job_id == job_id
            and record.status == ApplicationApprovalStatus.PENDING
        ]

        if not matches:
            return None

        return max(matches, key=lambda record: record.id or 0)

    def list_pending(self) -> list[ApplicationApprovalRecord]:
        return [
            record
            for record in self.records.values()
            if record.status == ApplicationApprovalStatus.PENDING
        ]

    def list_approved(self) -> list[ApplicationApprovalRecord]:
        return [
            record
            for record in self.records.values()
            if record.status == ApplicationApprovalStatus.APPROVED
            and record.consumed_at is None
        ]

    def approve(self, approval_id: int, approved_at: datetime) -> None:
        record = self.records[approval_id]

        self.records[approval_id] = ApplicationApprovalRecord(
            job_id=record.job_id,
            source=record.source,
            source_job_id=record.source_job_id,
            job_title=record.job_title,
            company=record.company,
            method=record.method,
            status=ApplicationApprovalStatus.APPROVED,
            id=record.id,
            apply_url=record.apply_url,
            recruiter_email=record.recruiter_email,
            reason=record.reason,
            created_at=record.created_at,
            approved_at=approved_at,
            rejected_at=record.rejected_at,
            consumed_at=record.consumed_at,
        )

    def reject(self, approval_id: int, rejected_at: datetime) -> None:
        record = self.records[approval_id]

        self.records[approval_id] = ApplicationApprovalRecord(
            job_id=record.job_id,
            source=record.source,
            source_job_id=record.source_job_id,
            job_title=record.job_title,
            company=record.company,
            method=record.method,
            status=ApplicationApprovalStatus.REJECTED,
            id=record.id,
            apply_url=record.apply_url,
            recruiter_email=record.recruiter_email,
            reason=record.reason,
            created_at=record.created_at,
            approved_at=record.approved_at,
            rejected_at=rejected_at,
            consumed_at=record.consumed_at,
        )

    def mark_consumed(
        self,
        approval_id: int,
        consumed_at: datetime,
    ) -> None:
        record = self.records[approval_id]

        self.records[approval_id] = ApplicationApprovalRecord(
            job_id=record.job_id,
            source=record.source,
            source_job_id=record.source_job_id,
            job_title=record.job_title,
            company=record.company,
            method=record.method,
            status=record.status,
            id=record.id,
            apply_url=record.apply_url,
            recruiter_email=record.recruiter_email,
            reason=record.reason,
            created_at=record.created_at,
            approved_at=record.approved_at,
            rejected_at=record.rejected_at,
            consumed_at=consumed_at,
        )


def make_job() -> Job:
    timestamp = datetime(2026, 8, 28, tzinfo=timezone.utc)

    return Job(
        title="Hardware Design Engineer",
        company="Test Electronics",
        location="Bengaluru, India",
        description="Design hardware and PCB systems.",
        source="test",
        source_job_id="APPROVAL-PHASE-001",
        source_url=HttpUrl(
            "https://example.com/careers/hardware-design-engineer/apply"
        ),
        employment_type="Full-time",
        experience_required="0-2 years",
        skills=["PCB Design", "Embedded C"],
        posted_at=timestamp,
        discovered_at=timestamp,
    )


def make_worker(
    approval_service: ApplicationApprovalService,
    job_repository: JobRepository,
    decision_repository: DecisionRepository,
    application_repository: ApplicationRepository,
    application_service: ApplicationService,
) -> WorkerCycle:
    settings = Mock(spec=Settings)
    client = Mock()

    return WorkerCycle(
        settings=settings,
        client=client,
        repository=job_repository,
        decision_repository=decision_repository,
        application_repository=application_repository,
        application_service=application_service,
        target_discovery=ApplyTargetDiscovery(),
        approval_service=approval_service,
    )


def test_worker_executes_approved_application() -> None:
    job = make_job()

    job_repository = Mock(spec=JobRepository)
    job_repository.get_by_source_job_id.return_value = job
    job_repository.get_id_by_source_job_id.return_value = 42

    decision = Mock()
    decision.action = DecisionAction.APPLY

    decision_repository = Mock(spec=DecisionRepository)
    decision_repository.list_for_job.return_value = [decision]

    application_repository = Mock(spec=ApplicationRepository)
    application_repository.has_submitted_application.return_value = False
    application_repository.get_latest.return_value = None

    application_service = Mock(spec=ApplicationService)
    application_service.submit.return_value = ApplicationResult(
        status=ApplicationStatus.SUBMITTED,
        method=ApplicationMethod.BROWSER,
        message="Application submitted.",
        external_reference="test-application-001",
    )

    approval_repository = FakeApprovalRepository()
    approval_service = ApplicationApprovalService(approval_repository)

    approval = approval_service.request(
        ApplicationApprovalRequest(
            source=job.source,
            source_job_id=job.source_job_id or "",
            job_title=job.title,
            company=job.company,
            application_method=ApplicationMethod.BROWSER,
            apply_url=str(job.source_url),
            reason="test approval",
        ),
        job_id=42,
    )

    assert approval.id is not None
    approval_id = approval.id
    approval_service.approve(approval_id)

    worker = make_worker(
        approval_service=approval_service,
        job_repository=job_repository,
        decision_repository=decision_repository,
        application_repository=application_repository,
        application_service=application_service,
    )

    worker.run_approval_phase()

    application_service.submit.assert_called_once()

    request = application_service.submit.call_args.kwargs["request"]

    assert request.source == job.source
    assert request.source_job_id == job.source_job_id
    assert request.application_method == ApplicationMethod.BROWSER
    assert request.apply_url == str(job.source_url)
    assert request.execution_mode.value == "full_auto"
    assert request.submission_authorized is True

    consumed_approval = approval_repository.get(approval_id)

    assert consumed_approval is not None
    assert consumed_approval.status == ApplicationApprovalStatus.APPROVED
    assert consumed_approval.consumed_at is not None

    assert approval_service.approved() == []


def test_worker_does_not_consume_approval_when_execution_fails() -> None:
    job = make_job()

    job_repository = Mock(spec=JobRepository)
    job_repository.get_by_source_job_id.return_value = job
    job_repository.get_id_by_source_job_id.return_value = 42

    decision = Mock()
    decision.action = DecisionAction.APPLY

    decision_repository = Mock(spec=DecisionRepository)
    decision_repository.list_for_job.return_value = [decision]

    application_repository = Mock(spec=ApplicationRepository)
    application_repository.has_submitted_application.return_value = False
    application_repository.get_latest.return_value = None

    application_service = Mock(spec=ApplicationService)
    application_service.submit.return_value = ApplicationResult(
        status=ApplicationStatus.PAUSED,
        method=ApplicationMethod.BROWSER,
        message="Browser execution requires manual recovery.",
    )

    approval_repository = FakeApprovalRepository()
    approval_service = ApplicationApprovalService(approval_repository)

    approval = approval_service.request(
        ApplicationApprovalRequest(
            source=job.source,
            source_job_id=job.source_job_id or "",
            job_title=job.title,
            company=job.company,
            application_method=ApplicationMethod.BROWSER,
            apply_url=str(job.source_url),
            reason="test approval",
        ),
        job_id=42,
    )

    assert approval.id is not None
    approval_id = approval.id
    approval_service.approve(approval_id)

    worker = make_worker(
        approval_service=approval_service,
        job_repository=job_repository,
        decision_repository=decision_repository,
        application_repository=application_repository,
        application_service=application_service,
    )

    worker.run_approval_phase()

    stored_approval = approval_repository.get(approval_id)

    assert stored_approval is not None
    assert stored_approval.status == ApplicationApprovalStatus.APPROVED
    assert stored_approval.consumed_at is None

    assert len(approval_service.approved()) == 1
