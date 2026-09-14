"""
Detect early-stage and emerging startup characteristics.

This module evaluates startup evidence only.

It does not:
- rank job opportunities,
- match candidates,
- make application decisions,
- send applications,
- or infer a company's age from its name.
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.opportunity.evidence import StartupEvidence


@dataclass(frozen=True)
class EarlyStageResult:
    """
    Result of early-stage / emerging startup evaluation.
    """

    is_early_or_emerging: bool
    confidence: str
    signals: tuple[str, ...]
    reasons: tuple[str, ...]


class EarlyStageStartupDetector:
    """
    Detects whether available evidence suggests that a company
    is early-stage or actively emerging.

    The detector is intentionally evidence-driven.
    """

    def evaluate(
        self,
        evidence: StartupEvidence,
    ) -> EarlyStageResult:
        signals: list[str] = []
        reasons: list[str] = []

        if evidence.recent_funding:
            signals.append("recent_funding")
            reasons.append("Recent funding activity detected.")

        if evidence.accelerator_or_incubator:
            signals.append("accelerator_or_incubator")
            reasons.append(
                "Accelerator or incubator participation detected."
            )

        if evidence.recent_product_launch:
            signals.append("recent_product_launch")
            reasons.append("Recent product launch detected.")

        if evidence.active_hardware_development:
            signals.append("active_hardware_development")
            reasons.append(
                "Active hardware development detected."
            )

        if evidence.recent_engineering_hiring:
            signals.append("recent_engineering_hiring")
            reasons.append(
                "Recent engineering hiring activity detected."
            )

        if evidence.technical_team_identified:
            signals.append("technical_team_identified")
            reasons.append(
                "A technical or engineering team has been identified."
            )

        if evidence.recent_company_activity:
            signals.append("recent_company_activity")
            reasons.append(
                "Recent company activity detected."
            )

        if evidence.engineering_contact_identified:
            signals.append("engineering_contact_identified")
            reasons.append(
                "An engineering contact has been identified."
            )

        signal_count = len(signals)

        # Strongest indicator of an emerging technical startup:
        # active product/hardware development combined with
        # growth/team activity.
        strong_growth = (
            evidence.active_hardware_development
            and (
                evidence.recent_funding
                or evidence.recent_engineering_hiring
                or evidence.recent_product_launch
            )
        )

        broad_growth = (
            evidence.recent_funding
            or evidence.recent_engineering_hiring
            or evidence.recent_product_launch
            or evidence.accelerator_or_incubator
        )

        technical_activity = (
            evidence.active_hardware_development
            or evidence.technical_team_identified
        )

        if strong_growth:
            return EarlyStageResult(
                is_early_or_emerging=True,
                confidence="HIGH",
                signals=tuple(signals),
                reasons=tuple(reasons),
            )

        if (
            technical_activity
            and broad_growth
            and signal_count >= 3
        ):
            return EarlyStageResult(
                is_early_or_emerging=True,
                confidence="HIGH",
                signals=tuple(signals),
                reasons=tuple(reasons),
            )

        if broad_growth and signal_count >= 2:
            return EarlyStageResult(
                is_early_or_emerging=True,
                confidence="MEDIUM",
                signals=tuple(signals),
                reasons=tuple(reasons),
            )

        if technical_activity and signal_count >= 2:
            return EarlyStageResult(
                is_early_or_emerging=True,
                confidence="MEDIUM",
                signals=tuple(signals),
                reasons=tuple(reasons),
            )

        if signal_count >= 1:
            return EarlyStageResult(
                is_early_or_emerging=False,
                confidence="LOW",
                signals=tuple(signals),
                reasons=tuple(reasons),
            )

        return EarlyStageResult(
            is_early_or_emerging=False,
            confidence="NONE",
            signals=(),
            reasons=(
                "Insufficient evidence to classify the company "
                "as early-stage or emerging.",
            ),
        )
