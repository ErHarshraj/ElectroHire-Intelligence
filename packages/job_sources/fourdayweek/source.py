from collections.abc import Iterator

from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.job_sources.fourdayweek.client import FourDayWeekClient
from packages.job_sources.fourdayweek.parser import parse_job
from packages.sources import SourceAdapter, SourceType


class FourDayWeekJobSource(JobSource, SourceAdapter):
    """Job source adapter for 4dayweek.io."""

    @property
    def name(self) -> str:
        return "fourdayweek"

    @property
    def source_type(self) -> SourceType:
        return SourceType.JOB

    def __init__(
        self,
        client: FourDayWeekClient,
        *,
        limit: int = 100,
    ) -> None:
        self.client = client
        self.limit = limit

    def fetch_jobs(self) -> Iterator[Job]:
        for item in self.client.fetch_jobs(limit=self.limit):
            yield parse_job(item)
