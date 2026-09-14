from packages.opportunity.early_stage import (
    EarlyStageStartupDetector,
)
from packages.opportunity.evidence import StartupEvidence


def test_hardware_startup_with_funding_is_high_confidence() -> None:
    evidence = StartupEvidence(
        recent_funding=True,
        active_hardware_development=True,
    )

    result = EarlyStageStartupDetector().evaluate(evidence)

    assert result.is_early_or_emerging is True
    assert result.confidence == "HIGH"
    assert "recent_funding" in result.signals
    assert "active_hardware_development" in result.signals


def test_hardware_startup_with_product_launch_and_hiring_is_high() -> None:
    evidence = StartupEvidence(
        recent_product_launch=True,
        active_hardware_development=True,
        recent_engineering_hiring=True,
    )

    result = EarlyStageStartupDetector().evaluate(evidence)

    assert result.is_early_or_emerging is True
    assert result.confidence == "HIGH"


def test_multiple_growth_signals_are_medium() -> None:
    evidence = StartupEvidence(
        recent_funding=True,
        accelerator_or_incubator=True,
    )

    result = EarlyStageStartupDetector().evaluate(evidence)

    assert result.is_early_or_emerging is True
    assert result.confidence == "MEDIUM"


def test_technical_team_and_activity_can_indicate_emerging_company() -> None:
    evidence = StartupEvidence(
        technical_team_identified=True,
        recent_engineering_hiring=True,
    )

    result = EarlyStageStartupDetector().evaluate(evidence)

    assert result.is_early_or_emerging is True
    assert result.confidence == "MEDIUM"


def test_single_weak_signal_is_not_enough() -> None:
    evidence = StartupEvidence(
        recent_company_activity=True,
    )

    result = EarlyStageStartupDetector().evaluate(evidence)

    assert result.is_early_or_emerging is False
    assert result.confidence == "LOW"


def test_no_evidence_returns_none_confidence() -> None:
    evidence = StartupEvidence()

    result = EarlyStageStartupDetector().evaluate(evidence)

    assert result.is_early_or_emerging is False
    assert result.confidence == "NONE"
    assert result.signals == ()


def test_no_job_signal_is_not_part_of_startup_detection() -> None:
    """
    Startup detection must not require an advertised job.

    A later opportunity layer can combine this result with
    the absence of a job and create a proactive outreach opportunity.
    """

    evidence = StartupEvidence(
        recent_funding=True,
        active_hardware_development=True,
    )

    result = EarlyStageStartupDetector().evaluate(evidence)

    assert result.is_early_or_emerging is True
