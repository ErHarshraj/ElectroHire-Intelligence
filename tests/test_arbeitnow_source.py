from datetime import datetime, timezone

from packages.job_sources.arbeitnow.parser import parse_job


def test_parse_job_maps_arbeitnow_fields() -> None:
    data = {
        "slug": "mechatronics-test-engineer-munich-bavaria-37664",
        "company_name": "Example Robotics GmbH",
        "title": "Mechatronics Test Engineer",
        "description": "<p>Design and test robotic systems.</p>",
        "remote": False,
        "url": (
            "https://www.arbeitnow.com/jobs/companies/"
            "example-robotics/mechatronics-test-engineer"
        ),
        "tags": [
            "Engineering",
            "Robotics",
            "Embedded Systems",
        ],
        "job_types": [
            "Full-time",
            "entry",
        ],
        "location": "Munich, Bavaria",
        "created_at": 1789917610,
    }

    job = parse_job(data)

    assert job.title == "Mechatronics Test Engineer"
    assert job.company == "Example Robotics GmbH"
    assert job.location == "Munich, Bavaria"
    assert job.description == "<p>Design and test robotic systems.</p>"

    assert job.source == "arbeitnow"
    assert job.source_job_id == (
        "mechatronics-test-engineer-munich-bavaria-37664"
    )
    assert str(job.source_url) == (
        "https://www.arbeitnow.com/jobs/companies/"
        "example-robotics/mechatronics-test-engineer"
    )

    assert job.employment_type == "Full-time"
    assert job.experience_required == "entry"
    assert job.skills == [
        "Engineering",
        "Robotics",
        "Embedded Systems",
    ]

    assert job.posted_at == datetime.fromtimestamp(
        1789917610,
        tz=timezone.utc,
    )

    assert job.discovered_at.tzinfo == timezone.utc
    assert job.is_active is True


def test_parse_job_handles_optional_fields() -> None:
    data = {
        "slug": "minimal-job-123",
        "company_name": "Minimal Company",
        "title": "Embedded Engineer",
        "description": None,
        "url": "https://www.arbeitnow.com/jobs/minimal-job-123",
        "location": None,
        "tags": None,
        "job_types": None,
        "created_at": None,
    }

    job = parse_job(data)

    assert job.title == "Embedded Engineer"
    assert job.company == "Minimal Company"
    assert job.location is None
    assert job.description is None
    assert job.skills == []
    assert job.employment_type is None
    assert job.experience_required is None
    assert job.posted_at is None


def test_parse_job_ignores_unknown_job_type_values() -> None:
    data = {
        "slug": "mixed-types-123",
        "company_name": "Example Company",
        "title": "Hardware Engineer",
        "url": "https://www.arbeitnow.com/jobs/mixed-types-123",
        "job_types": [
            "Full-time",
            "entry",
            "unknown-classification",
        ],
        "tags": [],
        "created_at": 1789917610,
    }

    job = parse_job(data)

    assert job.employment_type == (
        "Full-time, unknown-classification"
    )
    assert job.experience_required == "entry"


def test_parse_job_handles_invalid_timestamp() -> None:
    data = {
        "slug": "invalid-date-123",
        "company_name": "Example Company",
        "title": "Electronics Engineer",
        "url": "https://www.arbeitnow.com/jobs/invalid-date-123",
        "created_at": "not-a-timestamp",
    }

    job = parse_job(data)

    assert job.posted_at is None


def test_arbeitnow_source_fetch_jobs() -> None:
    from packages.job_sources.arbeitnow.source import ArbeitnowJobSource

    class FakeClient:
        def __init__(self) -> None:
            self.received_pages: int | None = None

        def fetch_jobs(
            self,
            *,
            pages: int = 1,
        ) -> list[dict[str, object]]:
            self.received_pages = pages

            return [
                {
                    "slug": "job-1",
                    "company_name": "Company One",
                    "title": "Hardware Engineer",
                    "url": "https://www.arbeitnow.com/jobs/job-1",
                    "job_types": ["Full-time", "entry"],
                    "tags": ["Hardware", "PCB"],
                    "created_at": 1789917610,
                },
                {
                    "slug": "job-2",
                    "company_name": "Company Two",
                    "title": "Embedded Engineer",
                    "url": "https://www.arbeitnow.com/jobs/job-2",
                    "job_types": ["Part-time", "senior"],
                    "tags": ["Embedded C"],
                    "created_at": 1789917610,
                },
            ]

    client = FakeClient()
    source = ArbeitnowJobSource(client, pages=3)

    jobs = list(source.fetch_jobs())

    assert client.received_pages == 3

    assert len(jobs) == 2
    assert jobs[0].title == "Hardware Engineer"
    assert jobs[0].source == "arbeitnow"
    assert jobs[1].title == "Embedded Engineer"
    assert jobs[1].source_job_id == "job-2"

    assert source.name == "arbeitnow"
    assert source.source_type.value == "job"


def test_client_follows_next_pagination(monkeypatch) -> None:
    from packages.job_sources.arbeitnow.client import ArbeitnowClient

    responses = [
        {
            "data": [
                {
                    "slug": "page-1-job",
                    "title": "Hardware Engineer",
                }
            ],
            "links": {
                "next": "https://www.arbeitnow.com/api/job-board-api?page=2",
            },
        },
        {
            "data": [
                {
                    "slug": "page-2-job",
                    "title": "Embedded Engineer",
                }
            ],
            "links": {
                "next": None,
            },
        },
    ]

    requested_urls: list[str] = []

    class FakeResponse:
        def __init__(self, data: dict[str, object]) -> None:
            self.data = data

        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, object]:
            return self.data

    def fake_get(
        url: str,
        *,
        timeout: float,
        headers: dict[str, str],
    ) -> FakeResponse:
        requested_urls.append(url)
        return FakeResponse(responses[len(requested_urls) - 1])

    monkeypatch.setattr(
        "packages.job_sources.arbeitnow.client.httpx.get",
        fake_get,
    )

    client = ArbeitnowClient()
    jobs = client.fetch_jobs(pages=5)

    assert len(jobs) == 2
    assert [job["slug"] for job in jobs] == [
        "page-1-job",
        "page-2-job",
    ]
    assert requested_urls == [
        "https://www.arbeitnow.com/api/job-board-api",
        "https://www.arbeitnow.com/api/job-board-api?page=2",
    ]


def test_client_stops_at_page_limit(monkeypatch) -> None:
    from packages.job_sources.arbeitnow.client import ArbeitnowClient

    requested_urls: list[str] = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, object]:
            return {
                "data": [
                    {
                        "slug": f"job-{len(requested_urls)}",
                        "title": "Engineer",
                    }
                ],
                "links": {
                    "next": (
                        "https://www.arbeitnow.com/api/"
                        "job-board-api?page=next"
                    ),
                },
            }

    def fake_get(
        url: str,
        *,
        timeout: float,
        headers: dict[str, str],
    ) -> FakeResponse:
        requested_urls.append(url)
        return FakeResponse()

    monkeypatch.setattr(
        "packages.job_sources.arbeitnow.client.httpx.get",
        fake_get,
    )

    client = ArbeitnowClient()
    jobs = client.fetch_jobs(pages=2)

    assert len(jobs) == 2
    assert len(requested_urls) == 2


def test_client_stops_when_next_is_missing(monkeypatch) -> None:
    from packages.job_sources.arbeitnow.client import ArbeitnowClient

    requested_urls: list[str] = []

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, object]:
            return {
                "data": [
                    {
                        "slug": "only-job",
                        "title": "Electronics Engineer",
                    }
                ],
                "links": {
                    "next": None,
                },
            }

    def fake_get(
        url: str,
        *,
        timeout: float,
        headers: dict[str, str],
    ) -> FakeResponse:
        requested_urls.append(url)
        return FakeResponse()

    monkeypatch.setattr(
        "packages.job_sources.arbeitnow.client.httpx.get",
        fake_get,
    )

    client = ArbeitnowClient()
    jobs = client.fetch_jobs(pages=5)

    assert len(jobs) == 1
    assert len(requested_urls) == 1
