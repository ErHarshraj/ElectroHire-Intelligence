from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.application.models import ApplicationMethod, ApplicationStatus
from packages.persistence.application_repository import (
    ApplicationRecord,
    ApplicationRepository,
)
from packages.persistence.models import ApplicationModel


class SQLAlchemyApplicationRepository(ApplicationRepository):
    """SQLAlchemy persistence for application attempts."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, record: ApplicationRecord) -> int:
        """Create and persist a new application attempt."""

        now = datetime.now(timezone.utc)

        application = ApplicationModel(
            job_id=record.job_id,
            method=record.method.value,
            status=record.status.value,
            apply_url=record.apply_url,
            recruiter_email=record.recruiter_email,
            external_reference=record.external_reference,
            message=record.message,
            started_at=record.started_at,
            submitted_at=record.submitted_at,
            created_at=now,
            updated_at=now,
        )

        self.session.add(application)
        self.session.flush()
        application_id = application.id
        self.session.commit()

        return application_id

    def get_latest(self, job_id: int) -> ApplicationRecord | None:
        """Return the latest application attempt for a job."""

        statement = (
            select(ApplicationModel)
            .where(ApplicationModel.job_id == job_id)
            .order_by(ApplicationModel.id.desc())
            .limit(1)
        )

        application = self.session.scalar(statement)

        if application is None:
            return None

        return self._to_record(application)

    def get_by_status(
        self,
        status: ApplicationStatus,
    ) -> list[ApplicationRecord]:
        """Return application attempts with the requested status."""

        statement = (
            select(ApplicationModel)
            .where(ApplicationModel.status == status.value)
            .order_by(ApplicationModel.id.asc())
        )

        applications = self.session.scalars(statement).all()

        return [
            self._to_record(application)
            for application in applications
        ]

    def list_active_attempts(self) -> list[ApplicationRecord]:
        """Return attempts requiring recovery before another submission."""

        active_statuses = (
            ApplicationStatus.PENDING.value,
            ApplicationStatus.IN_PROGRESS.value,
            ApplicationStatus.PAUSED.value,
        )

        statement = (
            select(ApplicationModel)
            .where(ApplicationModel.status.in_(active_statuses))
            .order_by(ApplicationModel.id.asc())
        )

        applications = self.session.scalars(statement).all()

        return [
            self._to_record(application)
            for application in applications
        ]

    def list_retryable_attempts(self) -> list[ApplicationRecord]:
        """Return failed attempts that are eligible for retry."""

        statement = (
            select(ApplicationModel)
            .where(
                ApplicationModel.status
                == ApplicationStatus.FAILED.value
            )
            .order_by(ApplicationModel.id.asc())
        )

        applications = self.session.scalars(statement).all()

        return [
            self._to_record(application)
            for application in applications
        ]

    def update(
        self,
        application_id: int,
        *,
        status: ApplicationStatus,
        message: str = "",
        external_reference: str | None = None,
        submitted_at: datetime | None = None,
    ) -> None:
        """Update an existing application attempt."""

        application = self.session.get(ApplicationModel, application_id)

        if application is None:
            raise ValueError(
                f"application attempt {application_id} does not exist"
            )

        application.status = status.value
        application.message = message
        application.external_reference = external_reference
        application.submitted_at = submitted_at
        application.updated_at = datetime.now(timezone.utc)

        self.session.commit()

    def has_submitted_application(self, job_id: int) -> bool:
        """Return whether the job already has a submitted application."""

        statement = select(ApplicationModel.id).where(
            ApplicationModel.job_id == job_id,
            ApplicationModel.status == ApplicationStatus.SUBMITTED.value,
        )

        return self.session.execute(statement).first() is not None

    @staticmethod
    def _to_record(application: ApplicationModel) -> ApplicationRecord:
        """Convert a database model into a domain persistence record."""

        return ApplicationRecord(
            job_id=application.job_id,
            method=ApplicationMethod(application.method),
            status=ApplicationStatus(application.status),
            id=application.id,
            apply_url=application.apply_url,
            recruiter_email=application.recruiter_email,
            external_reference=application.external_reference,
            message=application.message,
            started_at=application.started_at,
            submitted_at=application.submitted_at,
        )
