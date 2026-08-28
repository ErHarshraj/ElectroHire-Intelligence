from pydantic import HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.domain.job import Job
from packages.persistence.job_repository import JobRepository
from packages.persistence.models import JobModel


class SQLAlchemyJobRepository(JobRepository):
    """SQLAlchemy implementation of the job repository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, job: Job) -> None:
        """Persist a domain job."""

        model = JobModel(
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            source=job.source,
            source_job_id=job.source_job_id,
            source_url=str(job.source_url),
            employment_type=job.employment_type,
            experience_required=job.experience_required,
            skills=",".join(job.skills),
            posted_at=job.posted_at,
            discovered_at=job.discovered_at,
            is_active=job.is_active,
        )

        self._session.add(model)
        self._session.commit()

    def get_by_source_job_id(
        self,
        source: str,
        source_job_id: str,
    ) -> Job | None:
        """Find a domain job by source and source-specific ID."""

        statement = select(JobModel).where(
            JobModel.source == source,
            JobModel.source_job_id == source_job_id,
        )

        model = self._session.scalar(statement)

        if model is None:
            return None

        return self._to_domain(model)

    def list_jobs(self) -> list[Job]:
        """Return all persisted jobs as domain objects."""

        statement = select(JobModel).order_by(JobModel.id)

        models = self._session.scalars(statement).all()

        return [self._to_domain(model) for model in models]

    @staticmethod
    def _to_domain(model: JobModel) -> Job:
        """Convert a persistence model into a domain object."""

        return Job(
            title=model.title,
            company=model.company,
            location=model.location,
            description=model.description,
            source=model.source,
            source_job_id=model.source_job_id,
            source_url=HttpUrl(model.source_url),
            employment_type=model.employment_type,
            experience_required=model.experience_required,
            skills=[
                skill
                for skill in model.skills.split(",")
                if skill
            ],
            posted_at=model.posted_at,
            discovered_at=model.discovered_at,
            is_active=model.is_active,
        )
