from collections.abc import Iterator

from packages.common.hopin_config import HopinConfig
from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.job_sources.hopin.client import HopinClient
from packages.job_sources.hopin.parser import parse_job
from packages.sources import SourceAdapter, SourceType


class HopinJobSource(JobSource, SourceAdapter):
    """Job source adapter for the public Hopin jobs API."""

    @property
    def name(self) -> str:
        return "hopin"

    @property
    def source_type(self) -> SourceType:
        return SourceType.JOB

    def __init__(
        self,
        client: HopinClient,
        config: HopinConfig,
    ) -> None:
        self.client = client
        self.config = config

    def fetch_jobs(self) -> Iterator[Job]:
        if self.config.endpoint == "jobs":
            records = self.client.fetch_jobs(
                industry=self.config.industry,
                location=self.config.location,
                work_type=self.config.work_type,
                role_type=self.config.role_type,
                unofficial=self.config.unofficial,
            )
        else:
            records = self.client.fetch_internships(
                industry=self.config.industry,
                location=self.config.location,
                work_type=self.config.work_type,
                role_type=self.config.role_type,
                unofficial=self.config.unofficial,
            )

        for item in records:
            yield parse_job(item)
