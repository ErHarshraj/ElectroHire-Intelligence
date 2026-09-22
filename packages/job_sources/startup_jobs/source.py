from __future__ import annotations

from collections.abc import Iterator

from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.job_sources.startup_jobs.client import StartupJobsClient
from packages.job_sources.startup_jobs.parser import parse_job
from packages.sources import SourceAdapter, SourceType


class StartupJobsJobSource(JobSource, SourceAdapter):
    """Job source adapter for Startup Jobs RSS role feeds."""

    @property
    def name(self) -> str:
        return "startup_jobs"

    @property
    def source_type(self) -> SourceType:
        return SourceType.JOB

    def __init__(
        self,
        client: StartupJobsClient,
        *,
        role: str,
    ) -> None:
        self.client = client
        self.role = role

    def fetch_jobs(self) -> Iterator[Job]:
        for item in self.client.fetch_jobs(role=self.role):
            yield parse_job(item)
