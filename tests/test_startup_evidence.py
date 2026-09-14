"""
Tests for startup and company evidence evaluation.
"""

from packages.opportunity.evidence import (
    StartupEvidence,
    StartupEvidenceEngine,
)
from packages.opportunity.models import Company


def test_hardware_startup_with_product_launch_gets_hardware_score():
    engine = StartupEvidenceEngine()

    result = engine.evaluate(
        Company(name="Example Robotics"),
        StartupEvidence(
            active_hardware_development=True,
            recent_product_launch=True,
        ),
    )

    assert result.hardware_product_evidence == 15


def test_recent_funding_and_activity_create_growth_signal():
    engine = StartupEvidenceEngine()

    result = engine.evaluate(
        Company(name="Example Energy"),
        StartupEvidence(
            recent_funding=True,
            accelerator_or_incubator=True,
            recent_engineering_hiring=True,
            recent_company_activity=True,
        ),
    )

    assert result.growth_signal == 10


def test_identified_engineering_team_is_positive_signal():
    engine = StartupEvidenceEngine()

    result = engine.evaluate(
        Company(name="Example Embedded"),
        StartupEvidence(
            technical_team_identified=True,
        ),
    )

    assert result.engineering_team_signal == 6


def test_engineering_hiring_without_identified_team_is_partial_signal():
    engine = StartupEvidenceEngine()

    result = engine.evaluate(
        Company(name="Example Robotics"),
        StartupEvidence(
            recent_engineering_hiring=True,
        ),
    )

    assert result.engineering_team_signal == 5


def test_engineering_team_and_hiring_create_strong_signal():
    engine = StartupEvidenceEngine()

    result = engine.evaluate(
        Company(name="Example Robotics"),
        StartupEvidence(
            technical_team_identified=True,
            recent_engineering_hiring=True,
        ),
    )

    assert result.engineering_team_signal == 10


def test_direct_engineering_contact_is_maximum_contactability():
    engine = StartupEvidenceEngine()

    result = engine.evaluate(
        Company(name="Example Robotics"),
        StartupEvidence(
            engineering_contact_identified=True,
        ),
    )

    assert result.contactability == 5


def test_company_website_provides_partial_contactability():
    engine = StartupEvidenceEngine()

    result = engine.evaluate(
        Company(
            name="Example Robotics",
            website="https://example.com",
        ),
        StartupEvidence(),
    )

    assert result.contactability == 2


def test_no_evidence_does_not_create_false_opportunity():
    engine = StartupEvidenceEngine()

    result = engine.evaluate(
        Company(
            name="Very New Startup",
            founded_year=2026,
        ),
        StartupEvidence(),
    )

    assert result.hardware_product_evidence == 0
    assert result.growth_signal == 0
    assert result.engineering_team_signal == 0
    assert result.contactability == 0


def test_company_age_alone_does_not_create_score():
    engine = StartupEvidenceEngine()

    result = engine.evaluate(
        Company(
            name="New Robotics Startup",
            founded_year=2026,
            industry="Robotics",
        ),
        StartupEvidence(),
    )

    assert result.hardware_product_evidence == 0
    assert result.growth_signal == 0
    assert result.engineering_team_signal == 0
