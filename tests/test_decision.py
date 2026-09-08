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


def decide(job: Job):
    relevance, ranking = evaluate(job)

    result = JobDecisionEngine().decide(
        job=job,
        relevance=relevance,
        ranking=ranking,
    )

    return relevance, ranking, result


def test_high_relevant_job_is_apply() -> None:
    job = make_job(
        "Hardware Design Engineer",
        "Design hardware, PCB and electronic circuits.",
    )

    relevance, ranking, result = decide(job)

    assert ranking.priority.lower() in {"high", "medium"}
    assert result.action == DecisionAction.APPLY


def test_medium_relevant_job_is_apply() -> None:
    job = make_job(
        "PCB Design Engineer",
        "PCB layout and hardware design.",
    )

    relevance, ranking, result = decide(job)

    assert ranking.priority.lower() in {"high", "medium"}
    assert result.action == DecisionAction.APPLY


def test_low_hardware_job_is_apply() -> None:
    job = make_job(
        "Electrical Design & Development Engineer",
        "Electrical hardware design and development.",
    )

    relevance, ranking, result = decide(job)

    assert ranking.priority.lower() == "low"
    assert result.action == DecisionAction.APPLY


def test_low_embedded_system_job_is_apply() -> None:
    job = make_job(
        "Embedded System Engineer",
        "Embedded system design and development.",
    )

    relevance, ranking, result = decide(job)

    assert ranking.priority.lower() == "low"
    assert result.action == DecisionAction.APPLY


def test_low_openbmc_firmware_job_is_alert() -> None:
    job = make_job(
        "Sr. OpenBMC Firmware Engineer",
        "OpenBMC and embedded firmware development.",
    )

    relevance, ranking, result = decide(job)

    assert ranking.priority.lower() == "low"
    assert result.action == DecisionAction.ALERT


def test_low_wireless_firmware_job_is_alert() -> None:
    job = make_job(
        "Senior Wireless Firmware Engineer",
        "Wireless embedded firmware development.",
    )

    relevance, ranking, result = decide(job)

    assert ranking.priority.lower() == "low"
    assert result.action == DecisionAction.ALERT


def test_low_generic_firmware_job_is_ignore() -> None:
    job = make_job(
        "Firmware Engineer",
        "Embedded firmware development.",
    )

    relevance, ranking, result = decide(job)

    assert ranking.priority.lower() == "low"
    assert result.action == DecisionAction.IGNORE


def test_irrelevant_job_is_ignored() -> None:
    job = make_job(
        "Account Manager",
        "Manage customer accounts and business development.",
    )

    relevance, ranking, result = decide(job)

    assert not relevance.is_relevant
    assert result.action == DecisionAction.IGNORE


def test_decision_is_explainable() -> None:
    job = make_job(
        "Hardware Design Engineer",
        "Design embedded hardware and PCB systems.",
    )

    _, _, result = decide(job)

    assert result.reasons
