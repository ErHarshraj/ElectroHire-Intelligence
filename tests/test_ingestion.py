from packages.ingestion.service import IngestionService
from packages.job_sources.mock import MockJobSource


def test_ingestion_service_fetches_jobs() -> None:
    service = IngestionService(MockJobSource())

    jobs = service.ingest()

    assert len(jobs) == 2
    assert jobs[0].source == "mock"
    assert jobs[0].source_job_id == "MOCK-001"
    assert jobs[1].source_job_id == "MOCK-002"
