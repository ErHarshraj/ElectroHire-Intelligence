from datetime import datetime, timezone

from packages.matching.decision import DecisionAction
from packages.persistence.decision_repository import (
    DecisionRepository,
    PersistedDecision,
)


class InMemoryDecisionRepository(DecisionRepository):
    """In-memory decision repository for tests."""

    def __init__(self) -> None:
        self.decisions: list[PersistedDecision] = []
        self._job_ids: dict[tuple[str, str], int] = {}

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
        key = (source, source_job_id)

        if key not in self._job_ids:
            self._job_ids[key] = len(self._job_ids) + 1

        self.decisions.append(
            PersistedDecision(
                job_id=self._job_ids[key],
                action=action,
                relevance_score=relevance_score,
                ranking_score=ranking_score,
                priority=priority,
                reasons=reasons,
                created_at=datetime.now(timezone.utc),
            )
        )

    def list_for_job(
        self,
        source: str,
        source_job_id: str,
    ) -> list[PersistedDecision]:
        job_id = self._job_ids.get((source, source_job_id))

        if job_id is None:
            return []

        return [
            decision
            for decision in self.decisions
            if decision.job_id == job_id
        ]
