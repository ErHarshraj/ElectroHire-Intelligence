from collections.abc import Iterator

from packages.domain.job import Job
from packages.job_sources.arbeitnow.client import ArbeitnowClient
from packages.job_sources.arbeitnow.parser import parse_job
from packages.job_sources.base import JobSource
from packages.sources import SourceAdapter, SourceType


class ArbeitnowJobSource(JobSource, SourceAdapter):
    """Job source adapter for Arbeitnow jobs."""

    @property
    def name(self) -> str:
        return "arbeitnow"

    @property
    def source_type(self) -> SourceType:
        return SourceType.JOB

    def __init__(
        self,
        client: ArbeitnowClient,
        *,
        pages: int = 1,
    ) -> None:
        self.client = client
        self.pages = pages

    def fetch_jobs(self) -> Iterator[Job]:
        for item in self.client.fetch_jobs(pages=self.pages):
            yield parse_job(item)
