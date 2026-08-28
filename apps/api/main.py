from collections.abc import Generator

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from packages.persistence.database import SessionLocal
from packages.persistence.sqlalchemy_job_repository import (
    SQLAlchemyJobRepository,
)

app = FastAPI(
    title="ElectroHire Intelligence API",
    version="0.1.0",
)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/jobs")
def list_jobs(
    session: Session = Depends(get_db),	 # noqa: B008
) -> list[dict[str, object]]:
    repository = SQLAlchemyJobRepository(session)

    jobs = repository.list_jobs()

    return [
        {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "source": job.source,
            "source_job_id": job.source_job_id,
            "source_url": str(job.source_url),
            "skills": job.skills,
            "is_active": job.is_active,
        }
        for job in jobs
    ]
