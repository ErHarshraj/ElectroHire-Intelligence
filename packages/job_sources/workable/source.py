from __future__ import annotations

from collections.abc import Iterator

from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.sources import SourceAdapter, SourceType

from .client import WorkableClient
from .parser import parse_workable_job


class WorkableJobSource(JobSource, SourceAdapter):
    """Job source adapter for configured public Workable career accounts."""

    name = "workable"
    source_type = SourceType.JOB

    def __init__(
        self,
        *,
        client: WorkableClient,
        company_name: str,
    ) -> None:
        self.client = client
        self.company_name = company_name

    def fetch_jobs(self) -> Iterator[Job]:
        """Fetch and parse all publicly exposed Workable jobs."""
        jobs = self.client.fetch_jobs()

        for data in jobs:
            yield parse_workable_job(
                data=data,
                company_name=self.company_name,
                source_name=self.name,
            )
