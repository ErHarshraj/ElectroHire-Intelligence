from collections.abc import Iterable

from packages.domain.job import Job
from packages.job_sources.base import JobSource


class ExampleJobSource(JobSource):
    @property
    def name(self) -> str:
        return "example"

    def fetch_jobs(self) -> Iterable[Job]:
        return []


def test_job_source_contract() -> None:
    source = ExampleJobSource()

    assert source.name == "example"
    assert list(source.fetch_jobs()) == []
