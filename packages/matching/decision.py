from dataclasses import dataclass
from enum import Enum

from packages.matching.ranking import RankingResult
from packages.matching.relevance import RelevanceResult


class DecisionAction(str, Enum):
    """Operational action recommended for a ranked job."""

    APPLY = "apply"
    ALERT = "alert"
    IGNORE = "ignore"


@dataclass(frozen=True)
class DecisionResult:
    """Final operational decision for a job."""

    action: DecisionAction
    reasons: list[str]


class JobDecisionEngine:
    """Convert relevance and ranking results into an operational decision."""

    def decide(
        self,
        relevance: RelevanceResult,
        ranking: RankingResult,
    ) -> DecisionResult:
        if not relevance.is_relevant:
            return DecisionResult(
                action=DecisionAction.IGNORE,
                reasons=["job is not relevant to the candidate"],
            )

        priority = ranking.priority.lower()

        if priority == "high":
            return DecisionResult(
                action=DecisionAction.APPLY,
                reasons=["high-priority match"],
            )

        if priority == "medium":
            return DecisionResult(
                action=DecisionAction.APPLY,
                reasons=["medium-priority application candidate"],
            )

        if priority == "very_low":
            return DecisionResult(
                action=DecisionAction.IGNORE,
                reasons=["very-low-priority match"],
            )

        return DecisionResult(
            action=DecisionAction.ALERT,
            reasons=["low-priority match requires contextual decision"],
        )
