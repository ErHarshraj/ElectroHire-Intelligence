from abc import ABC, abstractmethod
from datetime import datetime

from packages.application.career_models import (
    CareerApplicationRecord,
    CareerApplicationStatus,
)


class CareerApplicationRepository(ABC):
    """Persistence interface for career-level application tracking."""

    @abstractmethod
    def save(self, record: CareerApplicationRecord) -> int:
        """Create and persist a career application."""

    @abstractmethod
    def get(self, application_id: int) -> CareerApplicationRecord | None:
        """Return a career application by its database ID."""

    @abstractmethod
    def get_by_job(self, job_id: int) -> CareerApplicationRecord | None:
        """Return the career application associated with a job."""

    @abstractmethod
    def list_by_status(
        self,
        status: CareerApplicationStatus,
    ) -> list[CareerApplicationRecord]:
        """Return career applications with the requested status."""

    @abstractmethod
    def update(
        self,
        application_id: int,
        *,
        status: CareerApplicationStatus,
        application_url: str | None = None,
        applied_at: datetime | None = None,
        notes: str = "",
        last_followup_at: datetime | None = None,
        next_followup_at: datetime | None = None,
    ) -> None:
        """Update an existing career application."""
