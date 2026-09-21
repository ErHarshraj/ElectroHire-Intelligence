
from packages.domain.job import Job
from packages.job_sources.ayla.source import AylaJobSource


class FakeAylaClient:
    def __init__(self) -> None:
        self.query: str | None = None
        self.limit: int | None = None

    def fetch_jobs(
        self,
        *,
        query: str,
        limit: int,
    ) -> list[dict]:
        self.query = query
        self.limit = limit

        return [
            {
                "id": "ayla-1",
                "title": "Hardware Engineer",
                "agency": "Example Electronics",
                "primaryLocationText": "Boston, MA",
                "description": "Hardware design role.",
                "sourceUrl": (
                    "https://example.com/jobs/"
                    "hardware-engineer"
                ),
                "employmentType": "full-time",
                "seniorityLevel": "entry",
                "skills": ["PCB Design", "Circuit Design"],
                "postedDate": "2026-09-20T10:00:00Z",
            },
        ]


def test_source_identity() -> None:
    client = FakeAylaClient()

    source = AylaJobSource(
        client=client,
        query="electronics",
        limit=50,
    )

    assert source.name == "ayla"
    assert source.source_type.value == "job"


def test_source_fetch_jobs() -> None:
    client = FakeAylaClient()

    source = AylaJobSource(
        client=client,
        query="hardware",
        limit=25,
    )

    jobs = list(source.fetch_jobs())

    assert len(jobs) == 1

    job = jobs[0]

    assert isinstance(job, Job)
    assert job.title == "Hardware Engineer"
    assert job.company == "Example Electronics"
    assert job.location == "Boston, MA"
    assert job.source == "ayla"
    assert job.source_job_id == "ayla-1"
    assert job.skills == [
        "PCB Design",
        "Circuit Design",
    ]

    assert client.query == "hardware"
    assert client.limit == 25


def test_source_passes_config_to_client() -> None:
    client = FakeAylaClient()

    source = AylaJobSource(
        client=client,
        query="embedded",
        limit=75,
    )

    list(source.fetch_jobs())

    assert client.query == "embedded"
    assert client.limit == 75
