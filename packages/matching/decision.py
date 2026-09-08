from dataclasses import dataclass
from enum import Enum

from packages.domain.job import Job
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


class DecisionPolicy:
    """Apply contextual rules to determine the operational action for a job."""

    APPLY_TITLE_KEYWORDS = (
        "hardware",
        "electronics",
        "pcb",
        "embedded system",
        "embedded systems",
        "electrical design",
    )

    ALERT_TITLE_KEYWORDS = (
        "openbmc",
        "bmc firmware",
        "wireless firmware",
        "embedded firmware",
    )

    GENERIC_FIRMWARE_KEYWORDS = (
        "firmware engineer",
        "firmware developer",
        "firmware lead",
        "firmware architect",
    )

    def decide(
        self,
        job: Job,
        relevance: RelevanceResult,
        ranking: RankingResult,
    ) -> DecisionResult:
        """Return the contextual operational decision for a job."""

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

        title = job.title.lower()

        if any(keyword in title for keyword in self.APPLY_TITLE_KEYWORDS):
            return DecisionResult(
                action=DecisionAction.APPLY,
                reasons=["low-priority role directly matches a target engineering area"],
            )

        if any(keyword in title for keyword in self.ALERT_TITLE_KEYWORDS):
            return DecisionResult(
                action=DecisionAction.ALERT,
                reasons=["low-priority role is a strong adjacent technical match"],
            )

        if any(keyword in title for keyword in self.GENERIC_FIRMWARE_KEYWORDS):
            return DecisionResult(
                action=DecisionAction.IGNORE,
                reasons=["low-priority firmware role is not sufficiently aligned"],
            )

        return DecisionResult(
            action=DecisionAction.IGNORE,
            reasons=["low-priority role lacks a sufficiently strong target-role signal"],
        )


class JobDecisionEngine:
    """Convert relevance and ranking results into an operational decision."""

    def __init__(self, policy: DecisionPolicy | None = None) -> None:
        self.policy = policy or DecisionPolicy()

    def decide(
        self,
        job: Job,
        relevance: RelevanceResult,
        ranking: RankingResult,
    ) -> DecisionResult:
        """Evaluate a job using relevance, ranking, and contextual policy."""

        return self.policy.decide(
            job=job,
            relevance=relevance,
            ranking=ranking,
        )
