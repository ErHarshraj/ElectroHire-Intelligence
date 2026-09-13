from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from packages.application.models import (
    ApplicationApprovalStatus,
    ApplicationMethod,
)


@dataclass(frozen=True)
class ApplicationApprovalRecord:
    """Persisted authorization request for a job application."""

    job_id: int
    source: str
    source_job_id: str
    job_title: str
    company: str
    method: ApplicationMethod
    status: ApplicationApprovalStatus
    id: int | None = None
    apply_url: str | None = None
    recruiter_email: str | None = None
    reason: str = ""
    created_at: datetime | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    consumed_at: datetime | None = None


class ApplicationApprovalRepository(ABC):
    """Persistence interface for application authorization requests."""

    @abstractmethod
    def save(self, record: ApplicationApprovalRecord) -> int:
        raise NotImplementedError

    @abstractmethod
    def get(self, approval_id: int) -> ApplicationApprovalRecord | None:
        raise NotImplementedError

    @abstractmethod
    def get_latest(self, job_id: int) -> ApplicationApprovalRecord | None:
        raise NotImplementedError

    @abstractmethod
    def get_pending(self, job_id: int) -> ApplicationApprovalRecord | None:
        raise NotImplementedError

    @abstractmethod
    def list_pending(self) -> list[ApplicationApprovalRecord]:
        raise NotImplementedError

    @abstractmethod
    def list_approved(self) -> list[ApplicationApprovalRecord]:
        raise NotImplementedError

    @abstractmethod
    def approve(self, approval_id: int, approved_at: datetime) -> None:
        raise NotImplementedError

    @abstractmethod
    def reject(self, approval_id: int, rejected_at: datetime) -> None:
        raise NotImplementedError

    @abstractmethod
    def mark_consumed(self, approval_id: int, consumed_at: datetime) -> None:
        raise NotImplementedError
