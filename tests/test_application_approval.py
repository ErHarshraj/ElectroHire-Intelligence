from datetime import datetime

import pytest

from packages.application.approval import ApplicationApprovalService
from packages.application.models import (
    ApplicationApprovalRequest,
    ApplicationApprovalStatus,
    ApplicationMethod,
)
from packages.persistence.application_approval_repository import (
    ApplicationApprovalRecord,
    ApplicationApprovalRepository,
)


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
        matches = [r for r in self.records.values() if r.job_id == job_id]
        return max(matches, key=lambda r: r.id or 0) if matches else None

    def get_pending(self, job_id: int) -> ApplicationApprovalRecord | None:
        matches = [
            r for r in self.records.values()
            if r.job_id == job_id and r.status == ApplicationApprovalStatus.PENDING
        ]
        return max(matches, key=lambda r: r.id or 0) if matches else None

    def list_pending(self) -> list[ApplicationApprovalRecord]:
        return [r for r in self.records.values() if r.status == ApplicationApprovalStatus.PENDING]

    def list_approved(self) -> list[ApplicationApprovalRecord]:
        return [
            r for r in self.records.values()
            if r.status == ApplicationApprovalStatus.APPROVED and r.consumed_at is None
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
        self.records[approval_id] = ApplicationApprovalRecord(
            **{**record.__dict__, "consumed_at": consumed_at}
        )


def make_request() -> ApplicationApprovalRequest:
    return ApplicationApprovalRequest(
        source="adzuna",
        source_job_id="approval-001",
        job_title="Hardware Design Engineer",
        company="Example Electronics",
        application_method=ApplicationMethod.EMAIL,
        recruiter_email="careers@example.com",
        reason="application requires explicit approval",
    )


def test_request_creates_pending_approval() -> None:
    repository = FakeApprovalRepository()
    service = ApplicationApprovalService(repository)

    approval = service.request(make_request(), job_id=42)

    assert approval.id == 1
    assert approval.job_id == 42
    assert approval.status == ApplicationApprovalStatus.PENDING
    assert approval.recruiter_email == "careers@example.com"


def test_duplicate_request_reuses_pending_approval() -> None:
    repository = FakeApprovalRepository()
    service = ApplicationApprovalService(repository)

    first = service.request(make_request(), job_id=42)
    second = service.request(make_request(), job_id=42)

    assert first.id == second.id
    assert len(repository.records) == 1


def test_approval_can_be_approved_once() -> None:
    repository = FakeApprovalRepository()
    service = ApplicationApprovalService(repository)

    pending = service.request(make_request(), job_id=42)
    approved = service.approve(pending.id or 0)

    assert approved.status == ApplicationApprovalStatus.APPROVED
    assert approved.approved_at is not None

    with pytest.raises(ValueError, match="not pending"):
        service.approve(pending.id or 0)


def test_approval_can_be_rejected_once() -> None:
    repository = FakeApprovalRepository()
    service = ApplicationApprovalService(repository)

    pending = service.request(make_request(), job_id=42)
    rejected = service.reject(pending.id or 0)

    assert rejected.status == ApplicationApprovalStatus.REJECTED
    assert rejected.rejected_at is not None


def test_rejected_approval_allows_new_request() -> None:
    repository = FakeApprovalRepository()
    service = ApplicationApprovalService(repository)

    first = service.request(make_request(), job_id=42)
    service.reject(first.id or 0)
    second = service.request(make_request(), job_id=42)

    assert second.id != first.id
    assert second.status == ApplicationApprovalStatus.PENDING
