from datetime import datetime, timedelta, timezone

from packages.domain.job import Job
from packages.matching.quality import JobQualityEngine

REFERENCE_TIME = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)


def make_job(**overrides) -> Job:
    data = {
        "title": "Embedded Hardware Engineer",
        "company": "Example Electronics Pvt. Ltd.",
        "location": "Bengaluru, India",
        "description": (
            "Design embedded hardware systems, review schematics and PCB layouts, "
            "work with microcontrollers, debug prototypes, develop and validate "
            "hardware designs, perform board bring-up and testing, investigate "
            "hardware failures, document engineering results, and collaborate "
            "with firmware, software, mechanical, and manufacturing teams."
        ),
        "source": "test",
        "source_job_id": "test-001",
        "source_url": "https://example.com/jobs/test-001",
        "employment_type": "Full-time",
        "experience_required": "0-2 years",
        "skills": ["Embedded C", "PCB Design", "Microcontrollers"],
        "posted_at": REFERENCE_TIME - timedelta(days=2),
        "discovered_at": REFERENCE_TIME,
    }

    data.update(overrides)
    return Job(**data)


def test_complete_fresh_job_gets_high_quality():
    engine = JobQualityEngine()

    result = engine.evaluate(
        make_job(),
        reference_time=REFERENCE_TIME,
    )

    assert result.score == 100
    assert result.quality == "HIGH"
    assert "Company is clearly identified" in result.reasons
    assert "Job posting is fresh" in result.reasons


def test_missing_optional_fields_does_not_crash():
    engine = JobQualityEngine()

    job = make_job(
        location=None,
        experience_required=None,
        employment_type=None,
        skills=[],
        posted_at=None,
    )

    result = engine.evaluate(
        job,
        reference_time=REFERENCE_TIME,
    )

    assert result.score >= 0
    assert result.score <= 100
    assert result.quality in {"HIGH", "MEDIUM", "LOW", "VERY_LOW"}


def test_short_description_reduces_quality():
    engine = JobQualityEngine()

    result = engine.evaluate(
        make_job(description="Hardware engineer required."),
        reference_time=REFERENCE_TIME,
    )

    assert result.score < 100
    assert "Job description is very short" in result.reasons


def test_medium_description_gets_limited_detail_score():
    engine = JobQualityEngine()

    description = (
        "Design and test embedded hardware systems, work with engineers on "
        "prototypes, perform debugging, and support hardware validation."
    )

    result = engine.evaluate(
        make_job(description=description),
        reference_time=REFERENCE_TIME,
    )

    assert "Job description contains limited detail" in result.reasons


def test_missing_description_gets_zero_description_points():
    engine = JobQualityEngine()

    result = engine.evaluate(
        make_job(description=None),
        reference_time=REFERENCE_TIME,
    )

    assert "Job description is missing" in result.reasons


def test_recent_job_gets_freshness_points():
    engine = JobQualityEngine()

    result = engine.evaluate(
        make_job(
            posted_at=REFERENCE_TIME - timedelta(days=5),
        ),
        reference_time=REFERENCE_TIME,
    )

    assert "Job posting is fresh" in result.reasons


def test_aging_job_gets_reduced_freshness_points():
    engine = JobQualityEngine()

    result = engine.evaluate(
        make_job(
            posted_at=REFERENCE_TIME - timedelta(days=20),
        ),
        reference_time=REFERENCE_TIME,
    )

    assert "Job posting is reasonably recent" in result.reasons


def test_stale_job_gets_no_freshness_points():
    engine = JobQualityEngine()

    result = engine.evaluate(
        make_job(
            posted_at=REFERENCE_TIME - timedelta(days=90),
        ),
        reference_time=REFERENCE_TIME,
    )

    assert "Job posting appears stale" in result.reasons


def test_quality_bands():
    engine = JobQualityEngine()

    assert engine._quality_band(100) == "HIGH"
    assert engine._quality_band(80) == "HIGH"
    assert engine._quality_band(79) == "MEDIUM"
    assert engine._quality_band(60) == "MEDIUM"
    assert engine._quality_band(59) == "LOW"
    assert engine._quality_band(40) == "LOW"
    assert engine._quality_band(39) == "VERY_LOW"
    assert engine._quality_band(0) == "VERY_LOW"


def test_future_posting_date_is_not_penalized():
    engine = JobQualityEngine()

    result = engine.evaluate(
        make_job(
            posted_at=REFERENCE_TIME + timedelta(days=1),
        ),
        reference_time=REFERENCE_TIME,
    )

    assert "Posting date appears fresh" in result.reasons
