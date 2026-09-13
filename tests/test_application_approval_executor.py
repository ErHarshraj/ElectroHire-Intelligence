from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from pydantic import HttpUrl

from packages.application.application_service import ApplicationService
from packages.application.approval import ApplicationApprovalService
from packages.application.approval_executor import ApplicationApprovalExecutor
from packages.application.discovery.target_discovery import ApplyTargetDiscovery
from packages.application.models import (
    ApplicationApprovalStatus,
    ApplicationMethod,
    ApplicationResult,
    ApplicationStatus,
)
from packages.domain.job import Job
from packages.matching.decision import DecisionAction
from packages.persistence.application_approval_repository import (
    ApplicationApprovalRecord,
    ApplicationApprovalRepository,
)
from packages.persistence.application_repository import ApplicationRepository
from packages.persistence.decision_repository import (
    DecisionRepository,
    PersistedDecision,
)
from packages.persistence.job_repository import JobRepository


class FakeApprovalRepository(ApplicationApprovalRepository):
    def __init__(self) -> None:
        self.records: dict[int, ApplicationApprovalRecord] = {}
        self.next_id = 1

    def save(self, record: ApplicationApprovalRecord) -> int:
        approval_id = self.next_id
        self.next_id += 1

        self.records[approval_id] = ApplicationApprovalRecord(
            **{**record.__dict__, "id": approval_id}
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
        return max(
            matches,
            key=lambda record: record.id or 0,
        ) if matches else None

    def get_pending(self, job_id: int) -> ApplicationApprovalRecord | None:
        matches = [
            record
            for record in self.records.values()
            if record.job_id == job_id
            and record.status == ApplicationApprovalStatus.PENDING
        ]
        return max(
            matches,
            key=lambda record: record.id or 0,
        ) if matches else None

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

        if record.status != ApplicationApprovalStatus.PENDING:
            raise ValueError("approval is not pending")

        self.records[approval_id] = ApplicationApprovalRecord(
            **{
                **record.__dict__,
                "status": ApplicationApprovalStatus.APPROVED,
                "approved_at": approved_at,
            }
        )

    def reject(self, approval_id: int, rejected_at: datetime) -> None:
        record = self.records[approval_id]

        if record.status != ApplicationApprovalStatus.PENDING:
            raise ValueError("approval is not pending")

        self.records[approval_id] = ApplicationApprovalRecord(
            **{
                **record.__dict__,
                "status": ApplicationApprovalStatus.REJECTED,
                "rejected_at": rejected_at,
            }
        )

    def mark_consumed(self, approval_id: int, consumed_at: datetime) -> None:
        record = self.records[approval_id]

        if record.status != ApplicationApprovalStatus.APPROVED:
            raise ValueError("approval is not approved")

        self.records[approval_id] = ApplicationApprovalRecord(
            **{
                **record.__dict__,
                "consumed_at": consumed_at,
            }
        )


def make_job(
    *,
    source_job_id: str = "approval-executor-001",
    source_url: str = "https://example.com/careers/apply/approval-executor-001",
    description: str = "Design embedded hardware and PCB layouts.",
    is_active: bool = True,
) -> Job:
    timestamp = datetime(2026, 9, 1, tzinfo=timezone.utc)

    return Job(
        title="Hardware Design Engineer",
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
        is_active=is_active,
    )


def make_approval(
    *,
    job_id: int = 1,
    source_job_id: str = "approval-executor-001",
    method: ApplicationMethod = ApplicationMethod.BROWSER,
    apply_url: str | None = (
        "https://example.com/careers/apply/approval-executor-001"
    ),
    recruiter_email: str | None = None,
) -> ApplicationApprovalRecord:
    return ApplicationApprovalRecord(
        job_id=job_id,
        source="test",
        source_job_id=source_job_id,
        job_title="Hardware Design Engineer",
        company="Test Electronics",
        method=method,
        status=ApplicationApprovalStatus.APPROVED,
        id=1,
        apply_url=apply_url,
        recruiter_email=recruiter_email,
        reason="explicit approval",
        created_at=datetime.now(timezone.utc),
        approved_at=datetime.now(timezone.utc),
    )


def make_decision(
    action: DecisionAction = DecisionAction.APPLY,
) -> PersistedDecision:
    return PersistedDecision(
        job_id=1,
        action=action,
        relevance_score=90.0,
        ranking_score=85.0,
        priority="HIGH",
        reasons=["Strong hardware match"],
        created_at=datetime.now(timezone.utc),
    )


def make_executor(
    *,
    job: Job | None = None,
    decision_action: DecisionAction = DecisionAction.APPLY,
    application_status: ApplicationStatus = ApplicationStatus.SUBMITTED,
) -> tuple[
    ApplicationApprovalExecutor,
    FakeApprovalRepository,
    Mock,
    Mock,
]:
    job = job or make_job()

    approval_repository = FakeApprovalRepository()
    approval_service = ApplicationApprovalService(approval_repository)

    job_repository = Mock(spec=JobRepository)
    job_repository.get_by_source_job_id.return_value = job
    job_repository.get_id_by_source_job_id.return_value = 1

    decision_repository = Mock(spec=DecisionRepository)
    decision_repository.list_for_job.return_value = [
        make_decision(decision_action)
    ]

    application_repository = Mock(spec=ApplicationRepository)
    application_service = Mock(spec=ApplicationService)
    application_service.submit.return_value = ApplicationResult(
        status=application_status,
        method=ApplicationMethod.BROWSER,
        message="application submitted",
        external_reference="test-reference",
    )

    executor = ApplicationApprovalExecutor(
        approval_service=approval_service,
        job_repository=job_repository,
        decision_repository=decision_repository,
        application_repository=application_repository,
        application_service=application_service,
        target_discovery=ApplyTargetDiscovery(),
    )

    return (
        executor,
        approval_repository,
        application_service,
        decision_repository,
    )


def test_approved_application_is_executed_and_consumed() -> None:
    executor, approval_repository, application_service, _ = make_executor()

    approval = make_approval()
    approval_repository.save(approval)

    result = executor.execute(approval)

    assert result == ApplicationStatus.SUBMITTED
    application_service.submit.assert_called_once()

    consumed = approval_repository.get(1)
    assert consumed is not None
    assert consumed.consumed_at is not None


def test_ignore_decision_blocks_execution() -> None:
    executor, approval_repository, application_service, _ = make_executor(
        decision_action=DecisionAction.IGNORE,
    )

    approval = make_approval()
    approval_repository.save(approval)

    with pytest.raises(
        ValueError,
        match="latest job decision no longer permits application",
    ):
        executor.execute(approval)

    application_service.submit.assert_not_called()

    stored = approval_repository.get(1)
    assert stored is not None
    assert stored.consumed_at is None


def test_inactive_job_blocks_execution() -> None:
    executor, approval_repository, application_service, _ = make_executor(
        job=make_job(is_active=False),
    )

    approval = make_approval()
    approval_repository.save(approval)

    with pytest.raises(
        ValueError,
        match="approved job is no longer active",
    ):
        executor.execute(approval)

    application_service.submit.assert_not_called()


def test_changed_application_target_blocks_execution() -> None:
    executor, approval_repository, application_service, _ = make_executor(
        job=make_job(
            source_url=(
                "https://example.com/careers/apply/changed-job"
            )
        ),
    )

    approval = make_approval()
    approval_repository.save(approval)

    with pytest.raises(
        ValueError,
        match="application target changed since approval",
    ):
        executor.execute(approval)

    application_service.submit.assert_not_called()


def test_failed_submission_does_not_consume_approval() -> None:
    executor, approval_repository, application_service, _ = make_executor(
        application_status=ApplicationStatus.FAILED,
    )

    approval = make_approval()
    approval_repository.save(approval)

    result = executor.execute(approval)

    assert result == ApplicationStatus.FAILED
    application_service.submit.assert_called_once()

    stored = approval_repository.get(1)
    assert stored is not None
    assert stored.consumed_at is None


def test_paused_submission_does_not_consume_approval() -> None:
    executor, approval_repository, application_service, _ = make_executor(
        application_status=ApplicationStatus.PAUSED,
    )

    approval = make_approval()
    approval_repository.save(approval)

    result = executor.execute(approval)

    assert result == ApplicationStatus.PAUSED
    application_service.submit.assert_called_once()

    stored = approval_repository.get(1)
    assert stored is not None
    assert stored.consumed_at is None


def test_already_submitted_consumes_approval() -> None:
    executor, approval_repository, application_service, _ = make_executor(
        application_status=ApplicationStatus.ALREADY_SUBMITTED,
    )

    approval = make_approval()
    approval_repository.save(approval)

    result = executor.execute(approval)

    assert result == ApplicationStatus.ALREADY_SUBMITTED

    stored = approval_repository.get(1)
    assert stored is not None
    assert stored.consumed_at is not None


def test_consumed_approval_cannot_execute_again() -> None:
    executor, approval_repository, application_service, _ = make_executor()

    approval = make_approval()
    approval_repository.save(approval)
    approval_service = ApplicationApprovalService(approval_repository)
    approval_service.consume(1)

    consumed = approval_repository.get(1)
    assert consumed is not None

    with pytest.raises(
        ValueError,
        match="has already been consumed",
    ):
        executor.execute(consumed)

    application_service.submit.assert_not_called()
