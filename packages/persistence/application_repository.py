from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from packages.application.models import (
    ApplicationMethod,
    ApplicationStatus,
)


@dataclass(frozen=True)
class ApplicationRecord:
    """Complete persisted application attempt."""

    job_id: int
    method: ApplicationMethod
    status: ApplicationStatus
    id: int | None = None
    apply_url: str | None = None
    recruiter_email: str | None = None
    external_reference: str | None = None
    message: str = ""
    started_at: datetime | None = None
    submitted_at: datetime | None = None


class ApplicationRepository(ABC):
    @abstractmethod
    def save(self, record: ApplicationRecord) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_latest(self, job_id: int) -> ApplicationRecord | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_status(
        self,
        status: ApplicationStatus,
    ) -> list[ApplicationRecord]:
        """Return application attempts with the requested status."""
        raise NotImplementedError

    @abstractmethod
    def list_active_attempts(self) -> list[ApplicationRecord]:
        """Return attempts requiring recovery before another submission."""
        raise NotImplementedError

    @abstractmethod
    def list_retryable_attempts(self) -> list[ApplicationRecord]:
        """Return failed attempts that are eligible for retry."""
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        application_id: int,
        *,
        status: ApplicationStatus,
        message: str = "",
        external_reference: str | None = None,
        submitted_at: datetime | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def has_submitted_application(self, job_id: int) -> bool:
        raise NotImplementedError
