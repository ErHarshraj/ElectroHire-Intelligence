"""
Job quality and trust evaluation.

Determines whether a job listing is sufficiently complete,
useful, and trustworthy for further processing.

This module is intentionally separate from:
- relevance: whether the job belongs to the target domain
- ranking: how well the job fits the candidate
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from packages.domain.job import Job


@dataclass(frozen=True)
class JobQualityResult:
    """Result of evaluating the quality of a job listing."""

    score: float
    quality: str
    reasons: list[str]


class JobQualityEngine:
    """Evaluates the completeness and freshness of a job listing."""

    FRESH_DAYS = 7
    AGING_DAYS = 30
    STALE_DAYS = 60

    def evaluate(
        self,
        job: Job,
        reference_time: datetime | None = None,
    ) -> JobQualityResult:
        """
        Evaluate job quality.

        Args:
            job: Canonical job representation.
            reference_time: Reference time used for freshness checks.
                Injected for deterministic testing.

        Returns:
            JobQualityResult containing score, quality band,
            and human-readable reasons.
        """
        now = reference_time or datetime.now()

        score = 0.0
        reasons: list[str] = []

        # Company identification
        if self._has_meaningful_text(job.company):
            score += 15
            reasons.append("Company is clearly identified")
        else:
            reasons.append("Company information is missing or unclear")

        # Job title
        if self._has_meaningful_text(job.title):
            score += 10
            reasons.append("Job title is clearly identified")
        else:
            reasons.append("Job title is missing or unclear")

        # Description
        description_score, description_reason = self._evaluate_description(
            job.description
        )
        score += description_score
        reasons.append(description_reason)

        # Skills
        if job.skills:
            score += 10
            reasons.append("Relevant skills are identified")
        else:
            reasons.append("No skills are explicitly identified")

        # Location
        if self._has_meaningful_text(job.location):
            score += 10
            reasons.append("Job location is provided")
        else:
            reasons.append("Job location is not provided")

        # Experience requirement
        if self._has_meaningful_text(job.experience_required):
            score += 10
            reasons.append("Experience requirement is provided")
        else:
            reasons.append("Experience requirement is not provided")

        # Employment type
        if self._has_meaningful_text(job.employment_type):
            score += 5
            reasons.append("Employment type is provided")
        else:
            reasons.append("Employment type is not provided")

        # Posting date
        if job.posted_at is not None:
            score += 5
            freshness_score, freshness_reason = self._evaluate_freshness(
                job.posted_at,
                now,
            )
            score += freshness_score
            reasons.append(freshness_reason)
        else:
            reasons.append("Posting date is not available")

        score = min(100.0, max(0.0, score))
        quality = self._quality_band(score)

        return JobQualityResult(
            score=score,
            quality=quality,
            reasons=reasons,
        )

    @staticmethod
    def _has_meaningful_text(value: str | None) -> bool:
        """Return True when text contains useful non-whitespace content."""
        return bool(value and value.strip())

    @staticmethod
    def _evaluate_description(
        description: str | None,
    ) -> tuple[float, str]:
        """Evaluate whether the description contains useful information."""
        if not description or not description.strip():
            return 0.0, "Job description is missing"

        length = len(description.strip())

        if length < 100:
            return 5.0, "Job description is very short"

        if length < 250:
            return 15.0, "Job description contains limited detail"

        return 25.0, "Job description contains useful detail"

    def _evaluate_freshness(
        self,
        posted_at: datetime,
        reference_time: datetime,
    ) -> tuple[float, str]:
        """Evaluate freshness based on posting age."""
        age = reference_time - posted_at

        if age < timedelta(days=0):
            return 10.0, "Posting date appears fresh"

        if age <= timedelta(days=self.FRESH_DAYS):
            return 10.0, "Job posting is fresh"

        if age <= timedelta(days=self.AGING_DAYS):
            return 5.0, "Job posting is reasonably recent"

        if age <= timedelta(days=self.STALE_DAYS):
            return 0.0, "Job posting is aging"

        return 0.0, "Job posting appears stale"

    @staticmethod
    def _quality_band(score: float) -> str:
        """Convert numeric quality score into a quality band."""
        if score >= 80:
            return "HIGH"

        if score >= 60:
            return "MEDIUM"

        if score >= 40:
            return "LOW"

        return "VERY_LOW"
