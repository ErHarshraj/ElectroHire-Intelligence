from datetime import datetime, timezone

from packages.application.career_models import (
    CareerApplicationRecord,
    CareerApplicationStatus,
    validate_career_application_transition,
)
from packages.persistence.career_application_repository import (
    CareerApplicationRepository,
)


class CareerApplicationService:
    """Application-layer service for career application tracking."""

    def __init__(
        self,
        repository: CareerApplicationRepository,
    ) -> None:
        self.repository = repository

    def create(
        self,
        *,
        job_id: int,
        status: CareerApplicationStatus = CareerApplicationStatus.SHORTLISTED,
        application_url: str | None = None,
        applied_at: datetime | None = None,
        notes: str = "",
    ) -> int:
        """Create a career application for a job."""

        existing = self.repository.get_by_job(job_id)

        if existing is not None:
            raise ValueError(
                f"career application already exists for job {job_id}"
            )

        now = datetime.now(timezone.utc)

        record = CareerApplicationRecord(
            job_id=job_id,
            status=status,
            application_url=application_url,
            applied_at=applied_at,
            notes=notes,
            created_at=now,
            updated_at=now,
        )

        return self.repository.save(record)

    def get(
        self,
        application_id: int,
    ) -> CareerApplicationRecord | None:
        """Return a career application by ID."""

        return self.repository.get(application_id)

    def get_by_job(
        self,
        job_id: int,
    ) -> CareerApplicationRecord | None:
        """Return the career application associated with a job."""

        return self.repository.get_by_job(job_id)

    def list_by_status(
        self,
        status: CareerApplicationStatus,
    ) -> list[CareerApplicationRecord]:
        """Return career applications with the requested status."""

        return self.repository.list_by_status(status)

    def transition(
        self,
        application_id: int,
        target_status: CareerApplicationStatus,
    ) -> None:
        """Transition a career application to a new lifecycle state."""

        application = self.repository.get(application_id)

        if application is None:
            raise ValueError(
                f"career application {application_id} does not exist"
            )

        validate_career_application_transition(
            application.status,
            target_status,
        )

        self.repository.update(
            application_id,
            status=target_status,
            application_url=application.application_url,
            applied_at=application.applied_at,
            notes=application.notes,
            last_followup_at=application.last_followup_at,
            next_followup_at=application.next_followup_at,
        )

    def mark_applied(
        self,
        application_id: int,
        applied_at: datetime,
    ) -> None:
        """Record the timestamp when an application was submitted."""

        application = self.repository.get(application_id)

        if application is None:
            raise ValueError(
                f"career application {application_id} does not exist"
            )

        self.repository.update(
            application_id,
            status=application.status,
            application_url=application.application_url,
            applied_at=applied_at,
            notes=application.notes,
            last_followup_at=application.last_followup_at,
            next_followup_at=application.next_followup_at,
        )

    def update_tracking(
        self,
        application_id: int,
        *,
        application_url: str | None = None,
        applied_at: datetime | None = None,
        notes: str = "",
        last_followup_at: datetime | None = None,
        next_followup_at: datetime | None = None,
    ) -> None:
        """Update tracking metadata without changing lifecycle status."""

        application = self.repository.get(application_id)

        if application is None:
            raise ValueError(
                f"career application {application_id} does not exist"
            )

        self.repository.update(
            application_id,
            status=application.status,
            application_url=application_url,
            applied_at=applied_at,
            notes=notes,
            last_followup_at=last_followup_at,
            next_followup_at=next_followup_at,
        )
