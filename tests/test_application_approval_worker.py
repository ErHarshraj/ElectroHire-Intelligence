from datetime import datetime, timezone
from unittest.mock import Mock

from pydantic import HttpUrl

from apps.worker.cycle import process_application
from packages.application.application_service import ApplicationService
from packages.application.approval import ApplicationApprovalService
from packages.application.discovery.target_discovery import ApplyTargetDiscovery
from packages.application.models import (
    ApplicationApprovalStatus,
    ApplicationExecutionMode,
)
from packages.domain.job import Job
from packages.matching.decision import DecisionAction
from packages.persistence.application_approval_repository import (
    ApplicationApprovalRecord,
    ApplicationApprovalRepository,
)
from packages.persistence.application_repository import ApplicationRepository
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
        matches = [record for record in self.records.values() if record.job_id == job_id]
        return max(matches, key=lambda record: record.id or 0) if matches else None

    def get_pending(self, job_id: int) -> ApplicationApprovalRecord | None:
        matches = [
            record
            for record in self.records.values()
            if record.job_id == job_id and record.status == ApplicationApprovalStatus.PENDING
        ]
        return max(matches, key=lambda record: record.id or 0) if matches else None

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
            if record.status == ApplicationApprovalStatus.APPROVED and record.consumed_at is None
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

    def mark_consumed(self, approval_id: int, consumed_at: datetime) -> None:
        raise NotImplementedError


def test_approval_required_worker_persists_request_without_submitting() -> None:
    job = Job(
        title="Hardware Design Engineer",
        company="Example Electronics",
        location="Indore",
        description="Design embedded hardware and PCB layouts.",
        source="test",
        source_job_id="approval-worker-001",
        source_url=HttpUrl("https://example.com/careers/apply/approval-worker-001"),
        discovered_at=datetime.now(timezone.utc),
    )

    job_repository = Mock(spec=JobRepository)
    job_repository.get_id_by_source_job_id.return_value = 42

    application_repository = Mock(spec=ApplicationRepository)
    application_repository.get_latest.return_value = None
    application_repository.has_submitted_application.return_value = False

    application_service = Mock(spec=ApplicationService)
    approval_repository = FakeApprovalRepository()
    approval_service = ApplicationApprovalService(approval_repository)

    result = process_application(
        job=job,
        decision_action=DecisionAction.APPLY,
        job_repository=job_repository,
        application_service=application_service,
        application_repository=application_repository,
        target_discovery=ApplyTargetDiscovery(),
        execution_mode=ApplicationExecutionMode.APPROVAL_REQUIRED,
        approval_service=approval_service,
    )

    assert result == "approval_pending"
    assert len(approval_repository.records) == 1

    approval = approval_repository.records[1]
    assert approval.status == ApplicationApprovalStatus.PENDING
    assert approval.job_id == 42
    assert approval.apply_url == str(job.source_url)
    application_service.submit.assert_not_called()
