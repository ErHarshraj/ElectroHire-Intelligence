from collections.abc import Iterator

from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.job_sources.remoteok.client import RemoteOKClient
from packages.job_sources.remoteok.parser import parse_job
from packages.sources import SourceAdapter, SourceType


class RemoteOKJobSource(JobSource, SourceAdapter):
    """Remote OK remote-job source."""

    @property
    def name(self) -> str:
        return "remoteok"

    @property
    def source_type(self) -> SourceType:
        return SourceType.JOB

    def __init__(
        self,
        client: RemoteOKClient,
    ) -> None:
        self.client = client

    def fetch_jobs(self) -> Iterator[Job]:
        """Fetch and parse jobs from Remote OK."""

        for item in self.client.fetch_jobs():
            yield parse_job(item)
