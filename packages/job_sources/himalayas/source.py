from __future__ import annotations

from collections.abc import Iterator

from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.job_sources.himalayas.client import HimalayasClient
from packages.job_sources.himalayas.parser import parse_job
from packages.sources import SourceAdapter, SourceType


class HimalayasJobSource(JobSource, SourceAdapter):
    """Himalayas remote-job source."""

    @property
    def name(self) -> str:
        return "himalayas"

    @property
    def source_type(self) -> SourceType:
        return SourceType.JOB

    def __init__(
        self,
        client: HimalayasClient,
        limit: int = 50,
    ) -> None:
        self.client = client
        self.limit = limit

    def fetch_jobs(self) -> Iterator[Job]:
        """Fetch all available Himalayas jobs using cursor pagination."""

        cursor: str | None = None

        while True:
            data = self.client.search_jobs(
                limit=self.limit,
                cursor=cursor,
            )

            jobs = data.get("jobs", [])

            if not isinstance(jobs, list):
                raise TypeError(
                    "Himalayas API jobs field must be a list."
                )

            for item in jobs:
                if not isinstance(item, dict):
                    raise TypeError(
                        "Himalayas API job record must be an object."
                    )

                yield parse_job(item)

            next_cursor = data.get("nextCursor")

            if not next_cursor:
                break

            cursor = str(next_cursor)
