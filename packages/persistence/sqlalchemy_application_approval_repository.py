from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.application.models import ApplicationApprovalStatus, ApplicationMethod
from packages.persistence.application_approval_repository import (
    ApplicationApprovalRecord,
    ApplicationApprovalRepository,
)
from packages.persistence.models import ApplicationApprovalModel


class SQLAlchemyApplicationApprovalRepository(ApplicationApprovalRepository):
    """SQLAlchemy persistence for application authorization requests."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, record: ApplicationApprovalRecord) -> int:
        now = datetime.now(timezone.utc)

        approval = ApplicationApprovalModel(
            job_id=record.job_id,
            source=record.source,
            source_job_id=record.source_job_id,
            job_title=record.job_title,
            company=record.company,
            method=record.method.value,
            status=record.status.value,
            apply_url=record.apply_url,
            recruiter_email=record.recruiter_email,
            reason=record.reason,
            created_at=record.created_at or now,
            approved_at=record.approved_at,
            rejected_at=record.rejected_at,
            consumed_at=record.consumed_at,
            updated_at=record.created_at or now,
        )

        self.session.add(approval)
        self.session.flush()
        approval_id = approval.id
        self.session.commit()
        return approval_id

    def get(self, approval_id: int) -> ApplicationApprovalRecord | None:
        approval = self.session.get(ApplicationApprovalModel, approval_id)
        return None if approval is None else self._to_record(approval)

    def get_latest(self, job_id: int) -> ApplicationApprovalRecord | None:
        statement = (
            select(ApplicationApprovalModel)
            .where(ApplicationApprovalModel.job_id == job_id)
            .order_by(ApplicationApprovalModel.id.desc())
            .limit(1)
        )
        approval = self.session.scalar(statement)
        return None if approval is None else self._to_record(approval)

    def get_pending(self, job_id: int) -> ApplicationApprovalRecord | None:
        statement = (
            select(ApplicationApprovalModel)
            .where(
                ApplicationApprovalModel.job_id == job_id,
                ApplicationApprovalModel.status == ApplicationApprovalStatus.PENDING.value,
            )
            .order_by(ApplicationApprovalModel.id.desc())
            .limit(1)
        )
        approval = self.session.scalar(statement)
        return None if approval is None else self._to_record(approval)

    def list_pending(self) -> list[ApplicationApprovalRecord]:
        return self._list_by_status(ApplicationApprovalStatus.PENDING)

    def list_approved(self) -> list[ApplicationApprovalRecord]:
        statement = (
            select(ApplicationApprovalModel)
            .where(
                ApplicationApprovalModel.status == ApplicationApprovalStatus.APPROVED.value,
                ApplicationApprovalModel.consumed_at.is_(None),
            )
            .order_by(ApplicationApprovalModel.id.asc())
        )
        return [self._to_record(item) for item in self.session.scalars(statement).all()]

    def approve(self, approval_id: int, approved_at: datetime) -> None:
        approval = self._require_pending(approval_id)
        approval.status = ApplicationApprovalStatus.APPROVED.value
        approval.approved_at = approved_at
        approval.updated_at = datetime.now(timezone.utc)
        self.session.commit()

    def reject(self, approval_id: int, rejected_at: datetime) -> None:
        approval = self._require_pending(approval_id)
        approval.status = ApplicationApprovalStatus.REJECTED.value
        approval.rejected_at = rejected_at
        approval.updated_at = datetime.now(timezone.utc)
        self.session.commit()

    def mark_consumed(self, approval_id: int, consumed_at: datetime) -> None:
        approval = self.session.get(ApplicationApprovalModel, approval_id)
        if approval is None:
            raise ValueError(f"application approval {approval_id} does not exist")
        if approval.status != ApplicationApprovalStatus.APPROVED.value:
            raise ValueError(f"application approval {approval_id} is not approved")
        approval.consumed_at = consumed_at
        approval.updated_at = datetime.now(timezone.utc)
        self.session.commit()

    def _require_pending(self, approval_id: int) -> ApplicationApprovalModel:
        approval = self.session.get(ApplicationApprovalModel, approval_id)
        if approval is None:
            raise ValueError(f"application approval {approval_id} does not exist")
        if approval.status != ApplicationApprovalStatus.PENDING.value:
            raise ValueError(
                f"application approval {approval_id} is not pending"
            )
        return approval

    def _list_by_status(
        self,
        status: ApplicationApprovalStatus,
    ) -> list[ApplicationApprovalRecord]:
        statement = (
            select(ApplicationApprovalModel)
            .where(ApplicationApprovalModel.status == status.value)
            .order_by(ApplicationApprovalModel.id.asc())
        )
        return [self._to_record(item) for item in self.session.scalars(statement).all()]

    @staticmethod
    def _to_record(approval: ApplicationApprovalModel) -> ApplicationApprovalRecord:
        return ApplicationApprovalRecord(
            job_id=approval.job_id,
            source=approval.source,
            source_job_id=approval.source_job_id,
            job_title=approval.job_title,
            company=approval.company,
            method=ApplicationMethod(approval.method),
            status=ApplicationApprovalStatus(approval.status),
            id=approval.id,
            apply_url=approval.apply_url,
            recruiter_email=approval.recruiter_email,
            reason=approval.reason,
            created_at=approval.created_at,
            approved_at=approval.approved_at,
            rejected_at=approval.rejected_at,
            consumed_at=approval.consumed_at,
        )
