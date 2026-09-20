from datetime import datetime, timezone

from packages.job_sources.jobicy.parser import parse_job
from packages.job_sources.jobicy.source import JobicyJobSource


def test_parse_job_maps_fields() -> None:
    data = {
        "id": 12345,
        "jobTitle": "Embedded Systems Engineer",
        "companyName": "Example Robotics",
        "jobGeo": "Worldwide",
        "jobDescription": "Build embedded systems.",
        "jobType": ["full-time", "contract"],
        "jobLevel": "Mid-level",
        "jobIndustry": ["Electronics", "Engineering"],
        "pubDate": "2025-10-09T12:00:00Z",
        "url": "https://jobicy.com/jobs/12345",
    }

    job = parse_job(data)

    assert job.title == "Embedded Systems Engineer"
    assert job.company == "Example Robotics"
    assert job.location == "Worldwide"
    assert job.description == "Build embedded systems."
    assert job.source == "jobicy"
    assert job.source_job_id == "12345"
    assert str(job.source_url) == "https://jobicy.com/jobs/12345"
    assert job.employment_type == "full-time, contract"
    assert job.experience_required == "Mid-level"
    assert job.skills == ["Electronics", "Engineering"]
    assert job.posted_at == datetime(
        2025,
        10,
        9,
        12,
        0,
        tzinfo=timezone.utc,
    )


def test_parse_job_uses_fallback_jobicy_url_when_url_missing() -> None:
    data = {
        "id": 12345,
        "jobTitle": "Hardware Engineer",
    }

    job = parse_job(data)

    assert str(job.source_url) == "https://jobicy.com/jobs/12345"


def test_parse_job_handles_missing_optional_fields() -> None:
    data = {
        "id": 12345,
        "jobTitle": "Electronics Engineer",
    }

    job = parse_job(data)

    assert job.company == "Unknown"
    assert job.location is None
    assert job.description is None
    assert job.employment_type is None
    assert job.experience_required is None
    assert job.skills == []
    assert job.posted_at is None


def test_parse_job_handles_invalid_timestamp() -> None:
    data = {
        "id": 12345,
        "jobTitle": "Embedded Engineer",
        "pubDate": "not-a-timestamp",
    }

    job = parse_job(data)

    assert job.posted_at is None


def test_parse_job_handles_timestamp_epoch() -> None:
    data = {
        "id": 12345,
        "jobTitle": "Embedded Engineer",
        "pubDate": 1760000000,
    }

    job = parse_job(data)

    assert job.posted_at == datetime.fromtimestamp(
        1760000000,
        tz=timezone.utc,
    )


def test_parse_job_handles_non_list_job_type() -> None:
    data = {
        "id": 12345,
        "jobTitle": "Embedded Engineer",
        "jobType": "full-time",
    }

    job = parse_job(data)

    assert job.employment_type is None


def test_parse_job_handles_non_list_industry() -> None:
    data = {
        "id": 12345,
        "jobTitle": "Embedded Engineer",
        "jobIndustry": "Electronics",
    }

    job = parse_job(data)

    assert job.skills == []


def test_parse_job_requires_job_title() -> None:
    data = {
        "id": 12345,
    }

    try:
        parse_job(data)
    except KeyError as exc:
        assert exc.args == ("jobTitle",)
    else:
        raise AssertionError("parse_job should require jobTitle")


def test_parse_job_requires_id() -> None:
    data = {
        "jobTitle": "Embedded Engineer",
    }

    try:
        parse_job(data)
    except KeyError as exc:
        assert exc.args == ("id",)
    else:
        raise AssertionError("parse_job should require id")


def test_source_fetch_jobs_parses_client_records() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.received_count: int | None = None

        def fetch_jobs(self, *, count: int = 200) -> list[dict[str, object]]:
            self.received_count = count

            return [
                {
                    "id": 1,
                    "jobTitle": "Embedded Engineer",
                },
                {
                    "id": 2,
                    "jobTitle": "PCB Engineer",
                },
            ]

    client = FakeClient()

    source = JobicyJobSource(
        client=client,  # type: ignore[arg-type]
        count=50,
    )

    jobs = list(source.fetch_jobs())

    assert client.received_count == 50
    assert len(jobs) == 2
    assert jobs[0].title == "Embedded Engineer"
    assert jobs[0].source == "jobicy"
    assert jobs[1].title == "PCB Engineer"
    assert jobs[1].source_job_id == "2"


def test_source_identity() -> None:
    class FakeClient:
        def fetch_jobs(
            self,
            *,
            count: int = 200,
        ) -> list[dict[str, object]]:
            return []

    source = JobicyJobSource(
        client=FakeClient(),  # type: ignore[arg-type]
    )

    assert source.name == "jobicy"
    assert source.source_type.value == "job"
