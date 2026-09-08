from dataclasses import dataclass

from packages.domain.job import Job
from packages.matching.profile import CandidateProfile
from packages.matching.relevance import JobRelevanceEngine, RelevanceResult


@dataclass(frozen=True)
class RankingResult:
    score: float
    priority: str
    reasons: list[str]


class JobRankingEngine:
    """
    Rank jobs using relevance plus explainable candidate-profile signals.

    Score budget:
        Relevance       40
        Role            25
        Technical       20
        Domain          10
        Experience       5
        ------------------
        Maximum        100
    """

    def __init__(
        self,
        profile: CandidateProfile | None = None,
        relevance_engine: JobRelevanceEngine | None = None,
    ) -> None:
        self.profile = profile or CandidateProfile()
        self.relevance_engine = relevance_engine or JobRelevanceEngine()

    def rank(
        self,
        job: Job,
        relevance: RelevanceResult | None = None,
    ) -> RankingResult:
        relevance_result = relevance or self.relevance_engine.evaluate(job)

        role_score, role_reason = self._score_roles(job.title.lower())

        skill_score, skill_reason = self._score_families(
            job=job,
            families=self.profile.skill_families,
            points_per_family=5.0,
            maximum=20.0,
            label="Technical skill families",
        )

        domain_score, domain_reason = self._score_families(
            job=job,
            families=self.profile.domain_families,
            points_per_family=3.0,
            maximum=10.0,
            label="Target domain families",
        )

        experience_score, experience_reason = self._score_experience(
            (job.experience_required or "").lower()
        )

        relevance_contribution = relevance_result.score * 0.40

        score = round(
            relevance_contribution
            + role_score
            + skill_score
            + domain_score
            + experience_score,
            2,
        )

        # Relevance remains the gatekeeper.
        # An explicitly irrelevant job cannot become a high-priority
        # opportunity through ranking signals alone.
        if not relevance_result.is_relevant:
            score = min(score, 35.0)

        score = max(0.0, min(100.0, score))

        reasons = [
            f"Relevance contribution: {relevance_result.score:.2f} × 40%",
            *[
                reason
                for reason in (
                    role_reason,
                    skill_reason,
                    domain_reason,
                    experience_reason,
                )
                if reason
            ],
        ]

        return RankingResult(
            score=score,
            priority=self._priority(score),
            reasons=reasons,
        )

    def _score_roles(self, title: str) -> tuple[float, str | None]:
        exact_matches = [
            role
            for role in self.profile.target_roles
            if role in title
        ]

        if exact_matches:
            return 25.0, f"Target role match: {exact_matches[0]}"

        family_matches: list[tuple[str, float]] = []

        for name, phrases, weight in self.profile.role_families:
            if any(phrase in title for phrase in phrases):
                family_matches.append((name, weight))

        # Compound-title handling.
        #
        # Examples:
        #   "Firmware Lead Engineer"
        #   "Firmware Design Engineer"
        #   "BMC/OpenBMC Firmware Lead Engineer"
        #
        # These titles contain the important role concept even though
        # "firmware engineer" is not a contiguous substring.
        if "firmware" in title and "engineer" in title:
            if not any(name == "firmware" for name, _ in family_matches):
                family_matches.append(("firmware", 18.0))

        # Hardware + robotics compound roles.
        #
        # Example:
        #   "Robotic Engineer-Hardware"
        #
        # Treat this as a meaningful robotics/hardware role rather than
        # requiring an exact phrase such as "robotics hardware engineer".
        if (
            ("robotic" in title or "robotics" in title)
            and "hardware" in title
        ):
            if not any(name == "robotics" for name, _ in family_matches):
                family_matches.append(("robotics", 18.0))

            if not any(name == "hardware" for name, _ in family_matches):
                family_matches.append(("hardware", 22.0))

        if not family_matches:
            return 0.0, None

        best_name, best_weight = max(
            family_matches,
            key=lambda item: item[1],
        )

        additional = [
            name
            for name, _ in family_matches
            if name != best_name
        ]

        reason = f"Role family match: {best_name}"

        if additional:
            reason += f" + {', '.join(additional[:3])}"

        return min(25.0, best_weight), reason

    @staticmethod
    def _job_text(job: Job) -> str:
        return " ".join(
            part
            for part in (
                job.title,
                job.description or "",
                " ".join(job.skills),
            )
            if part
        ).lower()

    def _score_families(
        self,
        job: Job,
        families: tuple[tuple[str, tuple[str, ...]], ...],
        points_per_family: float,
        maximum: float,
        label: str,
    ) -> tuple[float, str | None]:
        text = self._job_text(job)

        matches = [
            name
            for name, phrases in families
            if any(phrase in text for phrase in phrases)
        ]

        if not matches:
            return 0.0, None

        score = min(
            maximum,
            len(matches) * points_per_family,
        )

        return (
            score,
            f"{label}: {', '.join(matches[:6])}",
        )

    def _score_experience(
        self,
        experience: str,
    ) -> tuple[float, str | None]:
        if not experience:
            return 0.0, None

        matches = [
            keyword
            for keyword in self.profile.experience_keywords
            if keyword in experience
        ]

        if not matches:
            return 0.0, None

        return 5.0, "Experience level appears compatible"

    @staticmethod
    def _priority(score: float) -> str:
        if score >= 80:
            return "HIGH"

        if score >= 60:
            return "MEDIUM"

        if score >= 40:
            return "LOW"

        return "VERY_LOW"
