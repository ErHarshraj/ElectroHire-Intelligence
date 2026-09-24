from __future__ import annotations

from collections.abc import Iterator

from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.sources import SourceAdapter, SourceType

from .client import RipplingClient
from .parser import parse_rippling_job


class RipplingJobSource(JobSource, SourceAdapter):
    """Job source adapter for configured public Rippling career boards."""

    name = "rippling"
    source_type = SourceType.JOB

    def __init__(
        self,
        *,
        client: RipplingClient,
        company_name: str,
    ) -> None:
        self.client = client
        self.company_name = company_name

    def fetch_jobs(self) -> Iterator[Job]:
        """Fetch, deduplicate, and parse Rippling jobs."""
        board_jobs = self.client.fetch_board_jobs()

        seen_ids: set[str] = set()

        for board_job in board_jobs:
            job_uuid = str(board_job.get("uuid") or "").strip()

            if not job_uuid or job_uuid in seen_ids:
                continue

            seen_ids.add(job_uuid)

            data = self.client.fetch_job_detail(job_uuid)

            yield parse_rippling_job(
                data=data,
                company_name=self.company_name,
                source_name=self.name,
            )
