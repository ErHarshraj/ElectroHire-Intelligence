"""
Tests for company and startup opportunity discovery.
"""

import pytest

from packages.opportunity.models import (
    Company,
    ContactMethod,
    Opportunity,
    OpportunitySignals,
    OpportunityStatus,
    OpportunityType,
)
from packages.opportunity.scoring import OpportunityScoringEngine


def test_company_can_represent_a_startup():
    company = Company(
        name="Example Robotics",
        website="https://example.com",
        location="Bengaluru",
        industry="Robotics",
        founded_year=2025,
        stage="Early Stage",
        signals=(
            "recent product launch",
            "new engineering hiring",
        ),
    )

    assert company.name == "Example Robotics"
    assert company.founded_year == 2025
    assert "recent product launch" in company.signals


def test_opportunity_does_not_require_advertised_job():
    company = Company(
        name="Example Embedded Systems",
        industry="Embedded Systems",
    )

    opportunity = Opportunity(
        company=company,
        opportunity_type=OpportunityType.PROACTIVE_OUTREACH,
        contact_method=ContactMethod.EMAIL,
        contact_target="founder@example.com",
        evidence=(
            "embedded product",
            "recent hardware launch",
        ),
    )

    assert opportunity.advertised_job_id is None
    assert opportunity.opportunity_type == OpportunityType.PROACTIVE_OUTREACH
    assert opportunity.status == OpportunityStatus.DISCOVERED


def test_high_opportunity_score():
    engine = OpportunityScoringEngine()

    result = engine.score(
        OpportunitySignals(
            technical_domain_fit=30,
            candidate_skill_fit=25,
            hardware_product_evidence=15,
            growth_signal=10,
            engineering_team_signal=10,
            location_fit=5,
            contactability=5,
        )
    )

    assert result.score == 100
    assert result.band == "HIGH"


def test_good_opportunity_score():
    engine = OpportunityScoringEngine()

    result = engine.score(
        OpportunitySignals(
            technical_domain_fit=25,
            candidate_skill_fit=20,
            hardware_product_evidence=10,
            growth_signal=5,
            engineering_team_signal=5,
            location_fit=3,
            contactability=2,
        )
    )

    assert result.score == 70
    assert result.band == "GOOD"


def test_watch_opportunity_score():
    engine = OpportunityScoringEngine()

    result = engine.score(
        OpportunitySignals(
            technical_domain_fit=18,
            candidate_skill_fit=12,
            hardware_product_evidence=6,
            growth_signal=3,
            engineering_team_signal=2,
            location_fit=1,
            contactability=1,
        )
    )

    assert result.score == 43
    assert result.band == "WATCH"


def test_ignore_opportunity_score():
    engine = OpportunityScoringEngine()

    result = engine.score(
        OpportunitySignals(
            technical_domain_fit=10,
            candidate_skill_fit=5,
            hardware_product_evidence=2,
            growth_signal=1,
            engineering_team_signal=0,
            location_fit=0,
            contactability=0,
        )
    )

    assert result.score == 18
    assert result.band == "IGNORE"


def test_negative_component_is_rejected():
    engine = OpportunityScoringEngine()

    with pytest.raises(ValueError, match="cannot be negative"):
        engine.score(
            OpportunitySignals(
                technical_domain_fit=-1,
            )
        )


def test_component_above_maximum_is_rejected():
    engine = OpportunityScoringEngine()

    with pytest.raises(ValueError, match="cannot exceed"):
        engine.score(
            OpportunitySignals(
                technical_domain_fit=31,
            )
        )


def test_reasons_are_generated():
    engine = OpportunityScoringEngine()

    result = engine.score(
        OpportunitySignals(
            technical_domain_fit=30,
            candidate_skill_fit=0,
        )
    )

    assert "Technical domain fit is strong" in result.reasons
    assert "Candidate skill fit has no supporting evidence" in result.reasons
