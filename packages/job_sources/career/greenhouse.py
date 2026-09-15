"""
Greenhouse public Job Board source.

Greenhouse publishes public job-board data through a read-only GET API.
No authentication is required for these public GET endpoints.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

import httpx

from packages.domain.job import Job
from packages.job_sources.career.base import CareerSiteJobSource
from packages.sources import SourceType


class GreenhouseJobSource(CareerSiteJobSource):
    """
    Discover published jobs from one company's Greenhouse job board.
    """

    name = "greenhouse"

    def __init__(
        self,
        company_name: str,
        board_token: str,
        timeout: float = 15.0,
    ) -> None:
        if not company_name.strip():
            raise ValueError("company_name must not be empty.")

        if not board_token.strip():
            raise ValueError("board_token must not be empty.")

        self._company_name = company_name.strip()
        self.board_token = board_token.strip()
        self.timeout = timeout

    @property
    def source_type(self) -> SourceType:
        return SourceType.JOB

    @property
    def company_name(self) -> str:
        return self._company_name

    @property
    def board_url(self) -> str:
        return (
            "https://boards-api.greenhouse.io/v1/boards/"
            f"{self.board_token}/jobs"
        )

    def fetch_jobs(self) -> Iterable[Job]:
        response = httpx.get(
            self.board_url,
            params={"content": "true"},
            timeout=self.timeout,
        )
        response.raise_for_status()

        payload = response.json()

        jobs = payload.get("jobs", [])

        if not isinstance(jobs, list):
            raise TypeError("Greenhouse jobs must be a list.")

        for item in jobs:
            if not isinstance(item, dict):
                raise TypeError("Greenhouse job must be an object.")

            yield self._parse_job(item)

    def _parse_job(self, item: dict) -> Job:
        location = item.get("location") or {}
        location_name = location.get("name")

        updated_at = self._parse_datetime(item.get("updated_at"))

        description = item.get("content") or ""

        source_job_id = str(item["id"])

        return Job(
            title=str(item.get("title") or "").strip(),
            company=self.company_name,
            location=str(location_name or "").strip(),
            description=description,
            source=self.name,
            source_job_id=source_job_id,
            source_url=item["absolute_url"],
            employment_type=None,
            experience_required=None,
            skills=[],
            posted_at=updated_at,
            discovered_at=datetime.now().astimezone(),
        )

    @staticmethod
    def _parse_datetime(value: object) -> datetime | None:
        if not isinstance(value, str) or not value.strip():
            return None

        return datetime.fromisoformat(value.replace("Z", "+00:00"))
