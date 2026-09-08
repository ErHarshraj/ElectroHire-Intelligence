import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.matching.decision import DecisionAction
from packages.persistence.decision_repository import (
    DecisionRepository,
    PersistedDecision,
)
from packages.persistence.models import JobDecisionModel, JobModel


class SQLAlchemyDecisionRepository(DecisionRepository):
    """SQLAlchemy implementation of the decision repository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save(
        self,
        source: str,
        source_job_id: str,
        action: DecisionAction,
        relevance_score: float,
        ranking_score: float,
        priority: str,
        reasons: list[str],
    ) -> None:
        job = self.session.scalar(
            select(JobModel).where(
                JobModel.source == source,
                JobModel.source_job_id == source_job_id,
            )
        )

        if job is None:
            raise ValueError(
                f"Cannot save decision: job not found "
                f"for source={source!r}, source_job_id={source_job_id!r}."
            )

        decision = JobDecisionModel(
            job_id=job.id,
            action=action.value,
            relevance_score=relevance_score,
            ranking_score=ranking_score,
            priority=priority,
            reasons=json.dumps(reasons),
            created_at=datetime.now(timezone.utc),
        )

        self.session.add(decision)
        self.session.commit()

    def list_for_job(
        self,
        source: str,
        source_job_id: str,
    ) -> list[PersistedDecision]:
        job = self.session.scalar(
            select(JobModel).where(
                JobModel.source == source,
                JobModel.source_job_id == source_job_id,
            )
        )

        if job is None:
            return []

        decisions = self.session.scalars(
            select(JobDecisionModel)
            .where(JobDecisionModel.job_id == job.id)
            .order_by(JobDecisionModel.id)
        ).all()

        return [
            PersistedDecision(
                job_id=decision.job_id,
                action=DecisionAction(decision.action),
                relevance_score=decision.relevance_score,
                ranking_score=decision.ranking_score,
                priority=decision.priority,
                reasons=json.loads(decision.reasons),
                created_at=decision.created_at,
            )
            for decision in decisions
        ]
