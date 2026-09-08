from datetime import datetime, timezone

from pydantic import HttpUrl

from packages.domain.job import Job
from packages.matching.decision import DecisionAction, JobDecisionEngine
from packages.matching.ranking import JobRankingEngine
from packages.matching.relevance import JobRelevanceEngine


def make_job(title: str, description: str = "") -> Job:
    return Job(
        title=title,
        company="Test Electronics",
        location="Bengaluru",
        description=description,
        source="test",
        source_job_id=title,
        source_url=HttpUrl("https://example.com/job"),
        skills=[],
        discovered_at=datetime.now(timezone.utc),
    )


def evaluate(job: Job):
    relevance = JobRelevanceEngine().evaluate(job)
    ranking = JobRankingEngine().rank(job)

    return relevance, ranking


def test_high_relevant_job_is_apply() -> None:
    job = make_job(
        "Hardware Design Engineer",
        "Design hardware, PCB and electronic circuits.",
    )

    relevance, ranking = evaluate(job)
    result = JobDecisionEngine().decide(relevance, ranking)

    assert ranking.priority.lower() in {"high", "medium"}
    assert result.action == DecisionAction.APPLY


def test_medium_relevant_job_is_apply() -> None:
    job = make_job(
        "PCB Design Engineer",
        "PCB layout and hardware design.",
    )

    relevance, ranking = evaluate(job)
    result = JobDecisionEngine().decide(relevance, ranking)

    assert ranking.priority.lower() in {"high", "medium"}
    assert result.action == DecisionAction.APPLY


def test_low_job_defaults_to_alert() -> None:
    job = make_job(
        "Firmware Engineer",
        "Embedded firmware development.",
    )

    relevance, ranking = evaluate(job)
    result = JobDecisionEngine().decide(relevance, ranking)

    assert ranking.priority.lower() == "low"
    assert result.action == DecisionAction.ALERT


def test_irrelevant_job_is_ignored() -> None:
    job = make_job(
        "Account Manager",
        "Manage customer accounts and business development.",
    )

    relevance, ranking = evaluate(job)
    result = JobDecisionEngine().decide(relevance, ranking)

    assert not relevance.is_relevant
    assert result.action == DecisionAction.IGNORE


def test_decision_is_explainable() -> None:
    job = make_job(
        "Hardware Design Engineer",
        "Design embedded hardware and PCB systems.",
    )

    relevance, ranking = evaluate(job)
    result = JobDecisionEngine().decide(relevance, ranking)

    assert result.reasons
