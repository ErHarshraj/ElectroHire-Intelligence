from datetime import datetime, timezone

import pytest
from pydantic import HttpUrl

from packages.domain.job import Job
from packages.domain.job_status import JobStatus
from packages.domain.lifecycle import (
    InvalidJobStatusTransition,
    JobLifecycle,
)


def create_job() -> Job:
    return Job(
        title="Hardware Design Engineer",
        company="Test Company",
        source="test",
        source_job_id="JOB-001",
        source_url=HttpUrl("https://example.com/jobs/JOB-001"),
        discovered_at=datetime.now(timezone.utc),
    )


def test_discovered_can_transition_to_evaluated() -> None:
    job = create_job()

    JobLifecycle().transition(job, JobStatus.EVALUATED)

    assert job.status == JobStatus.EVALUATED


def test_evaluated_can_transition_to_shortlisted() -> None:
    job = create_job()
    lifecycle = JobLifecycle()

    lifecycle.transition(job, JobStatus.EVALUATED)
    lifecycle.transition(job, JobStatus.SHORTLISTED)

    assert job.status == JobStatus.SHORTLISTED


def test_evaluated_can_transition_to_ignored() -> None:
    job = create_job()
    lifecycle = JobLifecycle()

    lifecycle.transition(job, JobStatus.EVALUATED)
    lifecycle.transition(job, JobStatus.IGNORED)

    assert job.status == JobStatus.IGNORED


def test_discovered_can_transition_directly_to_ignored() -> None:
    job = create_job()

    JobLifecycle().transition(job, JobStatus.IGNORED)

    assert job.status == JobStatus.IGNORED


def test_invalid_transition_raises_error() -> None:
    job = create_job()

    with pytest.raises(InvalidJobStatusTransition):
        JobLifecycle().transition(job, JobStatus.SHORTLISTED)


def test_ignored_cannot_transition() -> None:
    job = create_job()
    lifecycle = JobLifecycle()

    lifecycle.transition(job, JobStatus.IGNORED)

    with pytest.raises(InvalidJobStatusTransition):
        lifecycle.transition(job, JobStatus.EVALUATED)


def test_shortlisted_cannot_return_to_evaluated() -> None:
    job = create_job()
    lifecycle = JobLifecycle()

    lifecycle.transition(job, JobStatus.EVALUATED)
    lifecycle.transition(job, JobStatus.SHORTLISTED)

    with pytest.raises(InvalidJobStatusTransition):
        lifecycle.transition(job, JobStatus.EVALUATED)
