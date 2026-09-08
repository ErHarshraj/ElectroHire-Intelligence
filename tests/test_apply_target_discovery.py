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


def test_discovers_browser_application_url():
    job = make_job(
        source_url="https://company.com/careers/apply/123"
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.BROWSER
    assert target.apply_url == "https://company.com/careers/apply/123"
    assert target.recruiter_email is None


def test_discovers_career_path():
    job = make_job(
        source_url="https://company.com/career/hardware-engineer"
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.BROWSER


def test_discovers_application_path():
    job = make_job(
        source_url="https://company.com/application/hardware-engineer"
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.BROWSER


def test_discovers_apply_path():
    job = make_job(
        source_url="https://company.com/apply/hardware-engineer"
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.BROWSER


def test_discovers_jobs_apply_path():
    job = make_job(
        source_url="https://company.com/jobs/apply/123"
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.BROWSER


def test_job_detail_url_is_not_treated_as_application_url():
    job = make_job(
        source_url="https://company.com/jobs/123"
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.NONE


def test_apply_in_query_string_is_not_treated_as_application_url():
    job = make_job(
        source_url="https://company.com/jobs/123?redirect=/apply"
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.NONE


def test_discovers_recruiter_email():
    job = make_job(
        description="Please send your application to hiring@example.com."
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.EMAIL
    assert target.recruiter_email == "hiring@example.com"


def test_email_is_normalized_to_lowercase():
    job = make_job(
        description="Send your application to Hiring@Example.COM."
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.EMAIL
    assert target.recruiter_email == "hiring@example.com"


def test_preferred_recruiting_email_beats_generic_email():
    job = make_job(
        description=(
            "For questions contact info@example.com. "
            "Applications should be sent to careers@example.com."
        )
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.EMAIL
    assert target.recruiter_email == "careers@example.com"


def test_non_generic_email_beats_generic_email():
    job = make_job(
        description=(
            "Contact info@example.com or engineer@example.com "
            "for more information."
        )
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.EMAIL
    assert target.recruiter_email == "engineer@example.com"


def test_generic_email_is_used_as_fallback():
    job = make_job(
        description="Contact info@example.com for more information."
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.EMAIL
    assert target.recruiter_email == "info@example.com"


def test_returns_none_when_no_target_exists():
    job = make_job(
        description="Hardware Design Engineer position."
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.NONE
    assert target.apply_url is None
    assert target.recruiter_email is None


def test_browser_target_has_priority_over_email():
    job = make_job(
        source_url="https://company.com/careers/apply/123",
        description="Contact hiring@example.com for questions.",
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.BROWSER
    assert target.apply_url == "https://company.com/careers/apply/123"
    assert target.recruiter_email is None


def test_duplicate_emails_do_not_change_selection():
    job = make_job(
        description=(
            "Contact info@example.com. "
            "Again contact info@example.com."
        )
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method == ApplicationTargetMethod.EMAIL
    assert target.recruiter_email == "info@example.com"
