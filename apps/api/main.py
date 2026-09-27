from collections.abc import Generator

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from packages.application.approval import ApplicationApprovalService
from packages.domain.job import Job
from packages.matching.decision import JobDecisionEngine
from packages.matching.quality import JobQualityEngine
from packages.matching.ranking import JobRankingEngine
from packages.matching.relevance import JobRelevanceEngine
from packages.persistence.database import SessionLocal
from packages.persistence.sqlalchemy_application_approval_repository import (
    SQLAlchemyApplicationApprovalRepository,
)
from packages.persistence.sqlalchemy_application_repository import (
    SQLAlchemyApplicationRepository,
)
from packages.persistence.sqlalchemy_career_application_repository import (
    SQLAlchemyCareerApplicationRepository,
)
from packages.persistence.sqlalchemy_decision_repository import (
    SQLAlchemyDecisionRepository,
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


def _build_job_intelligence(
    session: Session,
    job_id: int,
    job: Job,
) -> dict[str, object]:
    """Build the complete read-side intelligence representation for a job."""

    relevance_engine = JobRelevanceEngine()
    ranking_engine = JobRankingEngine(
        relevance_engine=relevance_engine,
    )
    quality_engine = JobQualityEngine()
    decision_engine = JobDecisionEngine()

    decision_repository = SQLAlchemyDecisionRepository(session)
    application_repository = SQLAlchemyApplicationRepository(session)
    career_repository = SQLAlchemyCareerApplicationRepository(session)

    relevance = relevance_engine.evaluate(job)
    ranking = ranking_engine.rank(job, relevance)
    quality = quality_engine.evaluate(job)
    decision = decision_engine.decide(
        job,
        relevance,
        ranking,
    )

    decision_history = []

    if job.source_job_id is not None:
        decision_history = decision_repository.list_for_job(
            job.source,
            job.source_job_id,
        )

    latest_application = application_repository.get_latest(job_id)
    career_application = career_repository.get_by_job(job_id)

    return {
        "id": job_id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "description": job.description,
        "source": job.source,
        "source_job_id": job.source_job_id,
        "source_url": str(job.source_url),
        "employment_type": job.employment_type,
        "experience_required": job.experience_required,
        "skills": job.skills,
        "posted_at": job.posted_at,
        "discovered_at": job.discovered_at,
        "is_active": job.is_active,
        "status": job.status.value,
        "quality": {
            "score": quality.score,
            "quality": quality.quality,
            "reasons": quality.reasons,
        },
        "relevance": {
            "score": relevance.score,
            "is_relevant": relevance.is_relevant,
            "reasons": relevance.reasons,
        },
        "ranking": {
            "score": ranking.score,
            "priority": ranking.priority,
            "reasons": ranking.reasons,
        },
        "decision": {
            "action": decision.action.value,
            "reasons": decision.reasons,
        },
        "decision_history": [
            {
                "job_id": item.job_id,
                "action": item.action.value,
                "relevance_score": item.relevance_score,
                "ranking_score": item.ranking_score,
                "priority": item.priority,
                "reasons": item.reasons,
                "created_at": item.created_at,
            }
            for item in decision_history
        ],
        "application": (
            {
                "id": latest_application.id,
                "method": latest_application.method.value,
                "status": latest_application.status.value,
                "apply_url": latest_application.apply_url,
                "recruiter_email": latest_application.recruiter_email,
                "external_reference": latest_application.external_reference,
                "message": latest_application.message,
                "started_at": latest_application.started_at,
                "submitted_at": latest_application.submitted_at,
            }
            if latest_application is not None
            else None
        ),
        "career_application": (
            {
                "id": career_application.id,
                "status": career_application.status.value,
                "application_url": career_application.application_url,
                "applied_at": career_application.applied_at,
                "notes": career_application.notes,
                "last_followup_at": career_application.last_followup_at,
                "next_followup_at": career_application.next_followup_at,
                "created_at": career_application.created_at,
                "updated_at": career_application.updated_at,
            }
            if career_application is not None
            else None
        ),
    }


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/jobs")
def list_jobs(
    session: Session = Depends(get_db),  # noqa: B008
) -> list[dict[str, object]]:
    repository = SQLAlchemyJobRepository(session)

    results: list[dict[str, object]] = []

    for job_id, job in repository.list_jobs_with_ids():
        results.append(
            _build_job_intelligence(
                session,
                job_id,
                job,
            )
        )

    return results


@app.get("/jobs/{job_id}")
def get_job(
    job_id: int,
    session: Session = Depends(get_db),  # noqa: B008
) -> dict[str, object]:
    repository = SQLAlchemyJobRepository(session)
    job = repository.get_by_id(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return _build_job_intelligence(
        session,
        job_id,
        job,
    )


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
