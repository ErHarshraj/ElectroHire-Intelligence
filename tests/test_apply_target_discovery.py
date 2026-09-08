from datetime import datetime, timezone

from packages.application.discovery.target import ApplicationTargetMethod
from packages.application.discovery.target_discovery import ApplyTargetDiscovery
from packages.domain.job import Job


def make_job(
    *,
    source_url: str = "https://example.com/job/123",
    description: str | None = None,
) -> Job:
    return Job(
        title="Hardware Design Engineer",
        company="Test Electronics",
        location="India",
        description=description,
        source="adzuna",
        source_job_id="123",
        source_url=source_url,
        discovered_at=datetime.now(timezone.utc),
    )


def test_discovers_browser_application_url() -> None:
    job = make_job(
        source_url="https://company.com/careers/apply/123",
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.BROWSER
    assert target.apply_url == "https://company.com/careers/apply/123"


def test_discovers_recruiter_email() -> None:
    job = make_job(
        description="Please send your application to hiring@example.com.",
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.EMAIL
    assert target.recruiter_email == "hiring@example.com"


def test_returns_none_when_no_target_exists() -> None:
    job = make_job(
        description="Hardware Design Engineer position.",
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.NONE
    assert target.apply_url is None
    assert target.recruiter_email is None


def test_browser_target_has_priority_over_email() -> None:
    job = make_job(
        source_url="https://company.com/careers/apply/123",
        description="Contact hiring@example.com for questions.",
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.BROWSER
    assert target.apply_url == "https://company.com/careers/apply/123"
    assert target.recruiter_email is None
