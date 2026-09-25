from datetime import datetime, timezone

from pydantic import HttpUrl

from packages.domain.job import Job
from packages.domain.job_dedup import (
    dedup_keys,
    metadata_dedup_key,
    normalize_job_url,
    normalize_text,
)


def make_job(
    *,
    source: str = "mock",
    url: str = "https://example.com/jobs/123?utm_source=test",
    location: str = "Bengaluru, India",
) -> Job:
    return Job(
        title="Embedded Hardware Engineer",
        company="Example Electronics",
        location=location,
        description="Design embedded hardware and PCB systems.",
        source=source,
        source_job_id=f"{source}-123",
        source_url=HttpUrl(url),
        discovered_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
    )


def test_normalize_text_collapses_case_and_whitespace() -> None:
    assert normalize_text("  Example &amp; Electronics  ") == "example & electronics"


def test_normalize_job_url_removes_tracking_parameters() -> None:
    assert normalize_job_url(
        "HTTPS://Example.com/jobs/123/?utm_source=test&ref=feed"
    ) == "https://example.com/jobs/123"


def test_metadata_dedup_key_includes_company_title_and_location() -> None:
    job = make_job()

    assert metadata_dedup_key(job) == (
        "meta:example electronics|embedded hardware engineer|bengaluru, india"
    )


def test_dedup_keys_include_url_and_metadata() -> None:
    keys = dedup_keys(make_job())

    assert keys[0] == "url:https://example.com/jobs/123"
    assert keys[1].startswith("meta:example electronics|")
