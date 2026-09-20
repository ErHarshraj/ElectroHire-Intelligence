from collections.abc import Iterator

from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.job_sources.jobicy.client import JobicyClient
from packages.job_sources.jobicy.parser import parse_job
from packages.sources import SourceAdapter, SourceType


class JobicyJobSource(JobSource, SourceAdapter):
    """Job source adapter for Jobicy remote jobs."""

    @property
    def name(self) -> str:
        return "jobicy"

    @property
    def source_type(self) -> SourceType:
        return SourceType.JOB

    def __init__(
        self,
        client: JobicyClient,
        *,
        count: int = 200,
    ) -> None:
        self.client = client
        self.count = count

    def fetch_jobs(self) -> Iterator[Job]:
        for item in self.client.fetch_jobs(count=self.count):
            yield parse_job(item)
