"""
Opportunity scoring engine.

Determines whether a company represents a worthwhile engineering
opportunity for further investigation or proactive outreach.

This is separate from:
- job relevance
- candidate-job ranking
- application execution
"""

from packages.opportunity.models import OpportunityScore, OpportunitySignals


class OpportunityScoringEngine:
    """Score a potential company opportunity."""

    MAX_TECHNICAL_DOMAIN_FIT = 30.0
    MAX_CANDIDATE_SKILL_FIT = 25.0
    MAX_HARDWARE_PRODUCT_EVIDENCE = 15.0
    MAX_GROWTH_SIGNAL = 10.0
    MAX_ENGINEERING_TEAM_SIGNAL = 10.0
    MAX_LOCATION_FIT = 5.0
    MAX_CONTACTABILITY = 5.0

    def score(self, signals: OpportunitySignals) -> OpportunityScore:
        """
        Calculate an opportunity score from independent evidence signals.
        """

        values = {
            "Technical domain fit": (
                signals.technical_domain_fit,
                self.MAX_TECHNICAL_DOMAIN_FIT,
            ),
            "Candidate skill fit": (
                signals.candidate_skill_fit,
                self.MAX_CANDIDATE_SKILL_FIT,
            ),
            "Hardware/product evidence": (
                signals.hardware_product_evidence,
                self.MAX_HARDWARE_PRODUCT_EVIDENCE,
            ),
            "Growth signal": (
                signals.growth_signal,
                self.MAX_GROWTH_SIGNAL,
            ),
            "Engineering team signal": (
                signals.engineering_team_signal,
                self.MAX_ENGINEERING_TEAM_SIGNAL,
            ),
            "Location fit": (
                signals.location_fit,
                self.MAX_LOCATION_FIT,
            ),
            "Contactability": (
                signals.contactability,
                self.MAX_CONTACTABILITY,
            ),
        }

        score = 0.0
        reasons: list[str] = []

        for name, (value, maximum) in values.items():
            validated = self._validate_component(name, value, maximum)
            score += validated

            if validated >= maximum * 0.8:
                reasons.append(f"{name} is strong")
            elif validated > 0:
                reasons.append(f"{name} provides some positive evidence")
            else:
                reasons.append(f"{name} has no supporting evidence")

        score = min(100.0, max(0.0, score))

        return OpportunityScore(
            score=score,
            band=self._band(score),
            reasons=tuple(reasons),
        )

    @staticmethod
    def _validate_component(
        name: str,
        value: float,
        maximum: float,
    ) -> float:
        """Validate and clamp one scoring component."""

        if value < 0:
            raise ValueError(f"{name} cannot be negative")

        if value > maximum:
            raise ValueError(
                f"{name} cannot exceed {maximum:.1f}"
            )

        return value

    @staticmethod
    def _band(score: float) -> str:
        """Convert score to an opportunity band."""

        if score >= 80:
            return "HIGH"

        if score >= 60:
            return "GOOD"

        if score >= 40:
            return "WATCH"

        return "IGNORE"
