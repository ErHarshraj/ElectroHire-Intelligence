from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from packages.matching.decision import DecisionAction
from packages.persistence.models import Base, JobModel
from packages.persistence.sqlalchemy_decision_repository import (
    SQLAlchemyDecisionRepository,
)


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture
def repository(session: Session) -> SQLAlchemyDecisionRepository:
    return SQLAlchemyDecisionRepository(session)


@pytest.fixture
def job(session: Session) -> JobModel:
    job = JobModel(
        title="Hardware Design Engineer",
        company="Test Electronics",
        location="India",
        description="Hardware design role",
        source="adzuna",
        source_job_id="test-123",
        source_url="https://example.com/job/test-123",
        employment_type=None,
        experience_required=None,
        skills="PCB,Embedded",
        posted_at=None,
        discovered_at=datetime.now(timezone.utc),
        is_active=True,
        status="evaluated",
    )

    session.add(job)
    session.commit()
    session.refresh(job)

    return job


def test_save_and_list_decision(
    repository: SQLAlchemyDecisionRepository,
    job: JobModel,
) -> None:
    repository.save(
        source="adzuna",
        source_job_id="test-123",
        action=DecisionAction.APPLY,
        relevance_score=85.0,
        ranking_score=91.5,
        priority="HIGH",
        reasons=[
            "high-priority match",
            "strong hardware design alignment",
        ],
    )

    decisions = repository.list_for_job(
        source="adzuna",
        source_job_id="test-123",
    )

    assert len(decisions) == 1

    decision = decisions[0]

    assert decision.job_id == job.id
    assert decision.action == DecisionAction.APPLY
    assert decision.relevance_score == 85.0
    assert decision.ranking_score == 91.5
    assert decision.priority == "HIGH"
    assert decision.reasons == [
        "high-priority match",
        "strong hardware design alignment",
    ]
    assert decision.created_at is not None


def test_decision_history_is_preserved(
    repository: SQLAlchemyDecisionRepository,
    job: JobModel,
) -> None:
    repository.save(
        source="adzuna",
        source_job_id="test-123",
        action=DecisionAction.ALERT,
        relevance_score=55.0,
        ranking_score=58.0,
        priority="LOW",
        reasons=["low-priority match requires contextual decision"],
    )

    repository.save(
        source="adzuna",
        source_job_id="test-123",
        action=DecisionAction.APPLY,
        relevance_score=78.0,
        ranking_score=82.0,
        priority="HIGH",
        reasons=["high-priority match"],
    )

    decisions = repository.list_for_job(
        source="adzuna",
        source_job_id="test-123",
    )

    assert len(decisions) == 2

    assert decisions[0].action == DecisionAction.ALERT
    assert decisions[0].priority == "LOW"

    assert decisions[1].action == DecisionAction.APPLY
    assert decisions[1].priority == "HIGH"


def test_unknown_job_returns_empty_history(
    repository: SQLAlchemyDecisionRepository,
) -> None:
    decisions = repository.list_for_job(
        source="adzuna",
        source_job_id="does-not-exist",
    )

    assert decisions == []


def test_save_unknown_job_raises_error(
    repository: SQLAlchemyDecisionRepository,
) -> None:
    with pytest.raises(ValueError, match="job not found"):
        repository.save(
            source="adzuna",
            source_job_id="does-not-exist",
            action=DecisionAction.IGNORE,
            relevance_score=10.0,
            ranking_score=15.0,
            priority="VERY_LOW",
            reasons=["very-low-priority match"],
        )
