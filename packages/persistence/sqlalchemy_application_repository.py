from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.application.models import ApplicationStatus
from packages.persistence.application_repository import (
    ApplicationRecord,
    ApplicationRepository,
)
from packages.persistence.models import ApplicationModel


class SQLAlchemyApplicationRepository(ApplicationRepository):
    """SQLAlchemy implementation of application persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, record: ApplicationRecord) -> None:
        """Persist an application record."""

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
        self.session.commit()

    def has_submitted_application(self, job_id: int) -> bool:
        """Return whether the job already has a submitted application."""

        statement = select(ApplicationModel.id).where(
            ApplicationModel.job_id == job_id,
            ApplicationModel.status == ApplicationStatus.SUBMITTED.value,
        )

        return self.session.execute(statement).first() is not None
