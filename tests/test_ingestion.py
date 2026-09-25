from packages.ingestion.service import IngestionService
from packages.job_sources.mock import MockJobSource
from packages.persistence.in_memory import InMemoryJobRepository


def test_ingestion_service_fetches_and_persists_jobs() -> None:
    repository = InMemoryJobRepository()
    service = IngestionService(
        MockJobSource(),
        repository,
    )

    jobs = service.ingest()

    assert len(jobs) == 2
    assert jobs[0].source == "mock"
    assert jobs[0].source_job_id == "MOCK-001"
    assert jobs[1].source_job_id == "MOCK-002"

    assert repository.list_jobs() == jobs


def test_ingestion_service_skips_existing_jobs() -> None:
    repository = InMemoryJobRepository()
    service = IngestionService(
        MockJobSource(),
        repository,
    )

    first_run = service.ingest()
    second_run = service.ingest()

    assert len(first_run) == 2
    assert second_run == []

    assert repository.list_jobs() == first_run


def test_ingestion_skips_cross_source_duplicate_by_canonical_url() -> None:
    from datetime import datetime, timezone

    from pydantic import HttpUrl

    from packages.domain.job import Job

    class FirstSource:
        name = "first"

        def fetch_jobs(self) -> list[Job]:
            return [
                Job(
                    title="Embedded Hardware Engineer",
                    company="Example Electronics",
                    location="Bengaluru, India",
                    description="Design embedded hardware.",
                    source=self.name,
                    source_job_id="FIRST-001",
                    source_url=HttpUrl("https://example.com/jobs/123"),
                    discovered_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
                )
            ]

    class SecondSource:
        name = "second"

        def fetch_jobs(self) -> list[Job]:
            return [
                Job(
                    title="Embedded Hardware Engineer",
                    company="Example Electronics",
                    location="Bengaluru, India",
                    description="Same opportunity from another source.",
                    source=self.name,
                    source_job_id="SECOND-999",
                    source_url=HttpUrl("https://example.com/jobs/123?utm_source=feed"),
                    discovered_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
                )
            ]

    repository = InMemoryJobRepository()

    assert len(IngestionService(FirstSource(), repository).ingest()) == 1
    assert IngestionService(SecondSource(), repository).ingest() == []
    assert len(repository.list_jobs()) == 1


def test_ingestion_skips_cross_source_duplicate_by_company_title_location() -> None:
    from datetime import datetime, timezone

    from pydantic import HttpUrl

    from packages.domain.job import Job

    class FirstSource:
        name = "first"

        def fetch_jobs(self) -> list[Job]:
            return [
                Job(
                    title="PCB Design Engineer",
                    company="Example Electronics",
                    location="Pune, India",
                    description="Design PCB assemblies.",
                    source=self.name,
                    source_job_id="FIRST-002",
                    source_url=HttpUrl("https://first.example/jobs/456"),
                    discovered_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
                )
            ]

    class SecondSource:
        name = "second"

        def fetch_jobs(self) -> list[Job]:
            return [
                Job(
                    title="PCB Design Engineer",
                    company="Example Electronics",
                    location="Pune, India",
                    description="The same opportunity on another source.",
                    source=self.name,
                    source_job_id="SECOND-456",
                    source_url=HttpUrl("https://second.example/jobs/789"),
                    discovered_at=datetime(2026, 9, 25, tzinfo=timezone.utc),
                )
            ]

    repository = InMemoryJobRepository()

    assert len(IngestionService(FirstSource(), repository).ingest()) == 1
    assert IngestionService(SecondSource(), repository).ingest() == []
    assert len(repository.list_jobs()) == 1
