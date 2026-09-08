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
    apply_url: str | None = None
    recruiter_email: str | None = None
    external_reference: str | None = None
    message: str = ""
    started_at: datetime | None = None
    submitted_at: datetime | None = None


class ApplicationRepository(ABC):
    """Persistence interface for application attempts."""

    @abstractmethod
    def save(self, record: ApplicationRecord) -> None:
        """Persist an application record."""
        raise NotImplementedError

    @abstractmethod
    def has_submitted_application(self, job_id: int) -> bool:
        """Return whether the job already has a submitted application."""
        raise NotImplementedError
