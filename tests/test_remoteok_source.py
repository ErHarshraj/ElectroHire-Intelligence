from datetime import datetime, timezone

from packages.job_sources.remoteok.parser import parse_job
from packages.job_sources.remoteok.source import RemoteOKJobSource


def test_parse_job_maps_fields() -> None:
    data = {
        "id": 12345,
        "position": "Embedded Systems Engineer",
        "company": "Example Robotics",
        "location": "Worldwide",
        "description": "Build embedded systems.",
        "tags": ["embedded", "c", "electronics"],
        "employment_type": "full-time",
        "epoch": 1760000000,
        "url": "https://remoteok.com/remote-jobs/12345",
    }

    job = parse_job(data)

    assert job.title == "Embedded Systems Engineer"
    assert job.company == "Example Robotics"
    assert job.location == "Worldwide"
    assert job.description == "Build embedded systems."
    assert job.source == "remoteok"
    assert job.source_job_id == "12345"
    assert str(job.source_url) == (
        "https://remoteok.com/remote-jobs/12345"
    )
    assert job.employment_type == "full-time"
    assert job.skills == ["embedded", "c", "electronics"]
    assert job.posted_at == datetime.fromtimestamp(
        1760000000,
        tz=timezone.utc,
    )


def test_parse_job_uses_apply_url_when_url_missing() -> None:
    data = {
        "id": 12345,
        "position": "Hardware Engineer",
        "apply_url": "https://example.com/apply",
    }

    job = parse_job(data)

    assert str(job.source_url) == "https://example.com/apply"


def test_parse_job_handles_missing_optional_fields() -> None:
    data = {
        "id": 12345,
        "position": "Electronics Engineer",
    }

    job = parse_job(data)

    assert job.company == "Unknown"
    assert job.location is None
    assert job.description is None
    assert job.employment_type is None
    assert job.experience_required is None
    assert job.skills == []
    assert job.posted_at is None


def test_source_fetch_jobs_parses_client_records() -> None:
    class FakeClient:
        def fetch_jobs(self) -> list[dict[str, object]]:
            return [
                {
                    "id": 1,
                    "position": "Embedded Engineer",
                },
                {
                    "id": 2,
                    "position": "PCB Engineer",
                },
            ]

    source = RemoteOKJobSource(
        client=FakeClient(),  # type: ignore[arg-type]
    )

    jobs = list(source.fetch_jobs())

    assert len(jobs) == 2
    assert jobs[0].title == "Embedded Engineer"
    assert jobs[0].source == "remoteok"
    assert jobs[1].title == "PCB Engineer"
    assert jobs[1].source_job_id == "2"


def test_source_identity() -> None:
    class FakeClient:
        def fetch_jobs(self) -> list[dict[str, object]]:
            return []

    source = RemoteOKJobSource(
        client=FakeClient(),  # type: ignore[arg-type]
    )

    assert source.name == "remoteok"
    assert source.source_type.value == "job"
