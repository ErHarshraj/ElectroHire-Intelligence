from packages.job_sources.fourdayweek.source import FourDayWeekJobSource


def test_source_fetch_jobs_parses_client_records() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.received_limit: int | None = None

        def fetch_jobs(
            self,
            *,
            limit: int = 100,
        ) -> list[dict[str, object]]:
            self.received_limit = limit

            return [
                {
                    "id": "job-1",
                    "title": "Embedded Engineer",
                    "url": (
                        "https://4dayweek.io/job/"
                        "embedded-engineer"
                    ),
                    "company": {
                        "name": "Example Electronics",
                    },
                },
                {
                    "id": "job-2",
                    "title": "PCB Engineer",
                    "url": (
                        "https://4dayweek.io/job/"
                        "pcb-engineer"
                    ),
                    "company": {
                        "name": "Example Robotics",
                    },
                },
            ]

    client = FakeClient()

    source = FourDayWeekJobSource(
        client=client,  # type: ignore[arg-type]
        limit=50,
    )

    jobs = list(source.fetch_jobs())

    assert client.received_limit == 50
    assert len(jobs) == 2

    assert jobs[0].title == "Embedded Engineer"
    assert jobs[0].company == "Example Electronics"
    assert jobs[0].source == "fourdayweek"
    assert jobs[0].source_job_id == "job-1"

    assert jobs[1].title == "PCB Engineer"
    assert jobs[1].company == "Example Robotics"
    assert jobs[1].source == "fourdayweek"
    assert jobs[1].source_job_id == "job-2"


def test_source_identity() -> None:
    class FakeClient:
        def fetch_jobs(
            self,
            *,
            limit: int = 100,
        ) -> list[dict[str, object]]:
            return []

    source = FourDayWeekJobSource(
        client=FakeClient(),  # type: ignore[arg-type]
    )

    assert source.name == "fourdayweek"
    assert source.source_type.value == "job"


def test_source_uses_default_limit() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.received_limit: int | None = None

        def fetch_jobs(
            self,
            *,
            limit: int = 100,
        ) -> list[dict[str, object]]:
            self.received_limit = limit
            return []

    client = FakeClient()

    source = FourDayWeekJobSource(
        client=client,  # type: ignore[arg-type]
    )

    list(source.fetch_jobs())

    assert client.received_limit == 100
