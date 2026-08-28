from packages.job_sources.mock import MockJobSource


def test_mock_job_source_returns_jobs() -> None:
    source = MockJobSource()

    jobs = source.fetch_jobs()

    assert len(jobs) == 2
    assert jobs[0].title == "Embedded Hardware Engineer"
    assert jobs[0].source == "mock"
    assert jobs[0].source_job_id == "MOCK-001"
    assert jobs[1].title == "PCB Design Engineer"
    assert jobs[1].source_job_id == "MOCK-002"
