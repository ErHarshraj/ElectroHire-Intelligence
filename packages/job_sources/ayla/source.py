from collections.abc import Iterator

from packages.domain.job import Job
from packages.job_sources.ayla.client import AylaClient
from packages.job_sources.ayla.parser import parse_job
from packages.job_sources.base import JobSource
from packages.sources import SourceAdapter, SourceType


class AylaJobSource(JobSource, SourceAdapter):
    """Job source adapter for the public AylaGov jobs API."""

    @property
    def name(self) -> str:
        return "ayla"

    @property
    def source_type(self) -> SourceType:
        return SourceType.JOB

    def __init__(
        self,
        client: AylaClient,
        *,
        query: str,
        limit: int = 100,
    ) -> None:
        self.client = client
        self.query = query
        self.limit = limit

    def fetch_jobs(self) -> Iterator[Job]:
        for item in self.client.fetch_jobs(
            query=self.query,
            limit=self.limit,
        ):
            yield parse_job(item)
