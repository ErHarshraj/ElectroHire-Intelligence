"""
Startup and company evidence evaluation.

Converts observable company information into structured
opportunity signals.

This module does not:
- search the web
- perform candidate matching
- rank jobs
- send applications

It only evaluates evidence that has already been discovered.
"""

from dataclasses import dataclass

from packages.opportunity.models import Company, OpportunitySignals


@dataclass(frozen=True)
class StartupEvidence:
    """
    Observable evidence about a company.

    These are deliberately factual signals rather than assumptions.
    """

    recent_funding: bool = False
    accelerator_or_incubator: bool = False
    recent_product_launch: bool = False
    active_hardware_development: bool = False
    recent_engineering_hiring: bool = False
    technical_team_identified: bool = False
    recent_company_activity: bool = False
    engineering_contact_identified: bool = False


class StartupEvidenceEngine:
    """Convert company evidence into opportunity scoring signals."""

    def evaluate(
        self,
        company: Company,
        evidence: StartupEvidence,
    ) -> OpportunitySignals:
        """
        Evaluate startup evidence.

        Company age is intentionally treated as supporting context,
        not as proof that the company is a good opportunity.
        """

        return OpportunitySignals(
            hardware_product_evidence=self._hardware_product_score(
                evidence
            ),
            growth_signal=self._growth_score(evidence),
            engineering_team_signal=self._engineering_team_score(
                evidence
            ),
            contactability=self._contactability_score(
                company,
                evidence,
            ),
        )

    @staticmethod
    def _hardware_product_score(
        evidence: StartupEvidence,
    ) -> float:
        """Score evidence that the company is building real hardware."""

        score = 0.0

        if evidence.active_hardware_development:
            score += 8.0

        if evidence.recent_product_launch:
            score += 7.0

        return min(15.0, score)

    @staticmethod
    def _growth_score(
        evidence: StartupEvidence,
    ) -> float:
        """Score evidence of current startup growth/activity."""

        score = 0.0

        if evidence.recent_funding:
            score += 4.0

        if evidence.accelerator_or_incubator:
            score += 2.0

        if evidence.recent_engineering_hiring:
            score += 2.0

        if evidence.recent_company_activity:
            score += 2.0

        return min(10.0, score)

    @staticmethod
    def _engineering_team_score(
        evidence: StartupEvidence,
    ) -> float:
        """Score evidence of an identifiable engineering organization."""

        if evidence.technical_team_identified and evidence.recent_engineering_hiring:
            return 10.0

        if evidence.technical_team_identified:
            return 6.0

        if evidence.recent_engineering_hiring:
            return 5.0

        return 0.0

    @staticmethod
    def _contactability_score(
        company: Company,
        evidence: StartupEvidence,
    ) -> float:
        """Score whether the company appears directly contactable."""

        if evidence.engineering_contact_identified:
            return 5.0

        if company.website:
            return 2.0

        return 0.0
