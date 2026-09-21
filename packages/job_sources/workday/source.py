from __future__ import annotations

from collections.abc import Iterator

from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.sources import SourceAdapter, SourceType

from .client import WorkdayClient
from .parser import parse_workday_job


class WorkdayJobSource(JobSource, SourceAdapter):
    """Job source adapter for configured public Workday career boards."""

    name = "workday"
    source_type = SourceType.JOB

    def __init__(
        self,
        *,
        client: WorkdayClient,
        company_name: str,
        batches: int = 1,
    ) -> None:
        self.client = client
        self.company_name = company_name
        self.batches = batches

    def fetch_jobs(self) -> Iterator[Job]:
        """Fetch and parse configured Workday jobs."""
        summaries = self.client.fetch_jobs(batches=self.batches)

        for summary in summaries:
            external_path = summary["externalPath"]

            detail = self.client.fetch_job_detail(
                external_path=external_path,
            )

            external_url = str(
                detail.get("externalUrl")
                or f"{self.client.base_url}{external_path}"
            )

            yield parse_workday_job(
                summary=summary,
                detail=detail,
                company_name=self.company_name,
                source_name=self.name,
                external_url=external_url,
            )
