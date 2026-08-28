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
