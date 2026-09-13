from datetime import datetime, timezone

from packages.application.models import (
    ApplicationApprovalRequest,
    ApplicationApprovalStatus,
)
from packages.persistence.application_approval_repository import (
    ApplicationApprovalRecord,
    ApplicationApprovalRepository,
)


class ApplicationApprovalService:
    """Manage explicit human authorization for job applications."""

    def __init__(self, repository: ApplicationApprovalRepository) -> None:
        self.repository = repository

    def request(
        self,
        request: ApplicationApprovalRequest,
        job_id: int,
    ) -> ApplicationApprovalRecord:
        existing = self.repository.get_latest(job_id)
        if existing is not None and existing.status in {
            ApplicationApprovalStatus.PENDING,
            ApplicationApprovalStatus.APPROVED,
        }:
            return existing

        record = ApplicationApprovalRecord(
            job_id=job_id,
            source=request.source,
            source_job_id=request.source_job_id,
            job_title=request.job_title,
            company=request.company,
            method=request.application_method,
            status=ApplicationApprovalStatus.PENDING,
            apply_url=request.apply_url,
            recruiter_email=request.recruiter_email,
            reason=request.reason,
            created_at=datetime.now(timezone.utc),
        )
        approval_id = self.repository.save(record)
        saved = self.repository.get(approval_id)
        if saved is None:
            raise RuntimeError("application approval was not persisted")
        return saved

    def approve(self, approval_id: int) -> ApplicationApprovalRecord:
        self._require(approval_id)
        self.repository.approve(approval_id, datetime.now(timezone.utc))
        return self._require(approval_id)

    def reject(self, approval_id: int) -> ApplicationApprovalRecord:
        self._require(approval_id)
        self.repository.reject(approval_id, datetime.now(timezone.utc))
        return self._require(approval_id)

    def pending(self) -> list[ApplicationApprovalRecord]:
        return self.repository.list_pending()

    def approved(self) -> list[ApplicationApprovalRecord]:
        return self.repository.list_approved()

    def _require(self, approval_id: int) -> ApplicationApprovalRecord:
        approval = self.repository.get(approval_id)
        if approval is None:
            raise ValueError(f"application approval {approval_id} does not exist")
        return approval
