from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.application.career_models import (
    CareerApplicationRecord,
    CareerApplicationStatus,
)
from packages.persistence.career_application_repository import (
    CareerApplicationRepository,
)
from packages.persistence.models import CareerApplicationModel


class SQLAlchemyCareerApplicationRepository(CareerApplicationRepository):
    """SQLAlchemy persistence for career-level applications."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(self, record: CareerApplicationRecord) -> int:
        """Create and persist a career application."""

        now = datetime.now(timezone.utc)

        application = CareerApplicationModel(
            job_id=record.job_id,
            status=record.status.value,
            application_url=record.application_url,
            applied_at=record.applied_at,
            notes=record.notes,
            last_followup_at=record.last_followup_at,
            next_followup_at=record.next_followup_at,
            created_at=record.created_at or now,
            updated_at=record.updated_at or now,
        )

        self.session.add(application)
        self.session.flush()
        application_id = application.id
        self.session.commit()

        return application_id

    def get(self, application_id: int) -> CareerApplicationRecord | None:
        """Return a career application by database ID."""

        application = self.session.get(
            CareerApplicationModel,
            application_id,
        )

        if application is None:
            return None

        return self._to_record(application)

    def get_by_job(self, job_id: int) -> CareerApplicationRecord | None:
        """Return the career application associated with a job."""

        statement = (
            select(CareerApplicationModel)
            .where(CareerApplicationModel.job_id == job_id)
            .limit(1)
        )

        application = self.session.scalar(statement)

        if application is None:
            return None

        return self._to_record(application)

    def list_by_status(
        self,
        status: CareerApplicationStatus,
    ) -> list[CareerApplicationRecord]:
        """Return career applications with the requested status."""

        statement = (
            select(CareerApplicationModel)
            .where(CareerApplicationModel.status == status.value)
            .order_by(CareerApplicationModel.id.asc())
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
        status: CareerApplicationStatus,
        application_url: str | None = None,
        applied_at: datetime | None = None,
        notes: str = "",
        last_followup_at: datetime | None = None,
        next_followup_at: datetime | None = None,
    ) -> None:
        """Update an existing career application."""

        application = self.session.get(
            CareerApplicationModel,
            application_id,
        )

        if application is None:
            raise ValueError(
                f"career application {application_id} does not exist"
            )

        application.status = status.value
        application.application_url = application_url
        application.applied_at = applied_at
        application.notes = notes
        application.last_followup_at = last_followup_at
        application.next_followup_at = next_followup_at
        application.updated_at = datetime.now(timezone.utc)

        self.session.commit()

    @staticmethod
    def _as_utc(value: datetime | None) -> datetime | None:
        """Return a datetime with an explicit UTC timezone."""

        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    @classmethod
    def _to_record(
        cls,
        application: CareerApplicationModel,
    ) -> CareerApplicationRecord:
        """Convert a database model into a domain persistence record."""

        return CareerApplicationRecord(
            job_id=application.job_id,
            status=CareerApplicationStatus(application.status),
            id=application.id,
            application_url=application.application_url,
            applied_at=cls._as_utc(application.applied_at),
            notes=application.notes,
            last_followup_at=cls._as_utc(application.last_followup_at),
            next_followup_at=cls._as_utc(application.next_followup_at),
            created_at=cls._as_utc(application.created_at),
            updated_at=cls._as_utc(application.updated_at),
        )
