from abc import ABC, abstractmethod
from datetime import datetime

from packages.matching.decision import DecisionAction


class PersistedDecision:
    """Persistence representation of an operational job decision."""

    def __init__(
        self,
        job_id: int,
        action: DecisionAction,
        relevance_score: float,
        ranking_score: float,
        priority: str,
        reasons: list[str],
        created_at: datetime,
    ) -> None:
        self.job_id = job_id
        self.action = action
        self.relevance_score = relevance_score
        self.ranking_score = ranking_score
        self.priority = priority
        self.reasons = reasons
        self.created_at = created_at


class DecisionRepository(ABC):
    """Abstract persistence interface for job decisions."""

    @abstractmethod
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
        """Persist a decision for a source job."""
        raise NotImplementedError

    @abstractmethod
    def list_for_job(
        self,
        source: str,
        source_job_id: str,
    ) -> list[PersistedDecision]:
        """Return decision history for a source job."""
        raise NotImplementedError
