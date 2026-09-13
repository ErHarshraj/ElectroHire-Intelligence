from collections.abc import Generator

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from packages.application.approval import ApplicationApprovalService
from packages.matching.relevance import JobRelevanceEngine
from packages.persistence.database import SessionLocal
from packages.persistence.sqlalchemy_application_approval_repository import (
    SQLAlchemyApplicationApprovalRepository,
)
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
    session: Session = Depends(get_db),  # noqa: B008
) -> list[dict[str, object]]:
    repository = SQLAlchemyJobRepository(session)
    relevance_engine = JobRelevanceEngine()

    jobs = repository.list_jobs()

    results: list[dict[str, object]] = []

    for job in jobs:
        relevance = relevance_engine.evaluate(job)

        results.append(
            {
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "source": job.source,
                "source_job_id": job.source_job_id,
                "source_url": str(job.source_url),
                "skills": job.skills,
                "is_active": job.is_active,
                "relevance": {
                    "score": relevance.score,
                    "is_relevant": relevance.is_relevant,
                    "reasons": relevance.reasons,
                },
            }
        )

    return results


@app.get("/applications/approvals")
def list_application_approvals(
    session: Session = Depends(get_db),  # noqa: B008
) -> list[dict[str, object | None]]:
    """List application approvals waiting for human authorization."""

    service = ApplicationApprovalService(
        SQLAlchemyApplicationApprovalRepository(session)
    )

    return [
        {
            "id": approval.id,
            "job_id": approval.job_id,
            "source": approval.source,
            "source_job_id": approval.source_job_id,
            "job_title": approval.job_title,
            "company": approval.company,
            "method": approval.method.value,
            "status": approval.status.value,
            "apply_url": approval.apply_url,
            "recruiter_email": approval.recruiter_email,
            "reason": approval.reason,
            "created_at": approval.created_at,
        }
        for approval in service.pending()
    ]


@app.post("/applications/approvals/{approval_id}/approve")
def approve_application(
    approval_id: int,
    session: Session = Depends(get_db),  # noqa: B008
) -> dict[str, object | None]:
    """Approve one pending application for later authorized execution."""

    service = ApplicationApprovalService(
        SQLAlchemyApplicationApprovalRepository(session)
    )
    approval = service.approve(approval_id)

    return {
        "id": approval.id,
        "status": approval.status.value,
        "approved_at": approval.approved_at,
    }


@app.post("/applications/approvals/{approval_id}/reject")
def reject_application(
    approval_id: int,
    session: Session = Depends(get_db),  # noqa: B008
) -> dict[str, object | None]:
    """Reject one pending application authorization request."""

    service = ApplicationApprovalService(
        SQLAlchemyApplicationApprovalRepository(session)
    )
    approval = service.reject(approval_id)

    return {
        "id": approval.id,
        "status": approval.status.value,
        "rejected_at": approval.rejected_at,
    }
