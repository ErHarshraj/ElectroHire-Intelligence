"""
Lever public career-board job source.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

import httpx

from packages.domain.job import Job
from packages.job_sources.career.base import CareerSiteJobSource
from packages.sources import SourceType


class LeverJobSource(CareerSiteJobSource):
    """Fetch published jobs from a company's public Lever career board."""

    name = "lever"

    def __init__(
        self,
        company_name: str,
        site: str,
        timeout: float = 15.0,
        page_size: int = 100,
    ) -> None:
        if not company_name.strip():
            raise ValueError("company_name must not be empty.")

        if not site.strip():
            raise ValueError("site must not be empty.")

        if page_size <= 0:
            raise ValueError("page_size must be greater than zero.")

        self._company_name = company_name.strip()
        self.site = site.strip()
        self.timeout = timeout
        self.page_size = page_size

    @property
    def source_type(self) -> SourceType:
        return SourceType.JOB

    @property
    def company_name(self) -> str:
        return self._company_name

    @property
    def board_url(self) -> str:
        return f"https://api.lever.co/v0/postings/{self.site}"

    def fetch_jobs(self) -> Iterable[Job]:
        """Fetch all currently published jobs from the Lever board."""

        skip = 0

        while True:
            response = httpx.get(
                self.board_url,
                params={
                    "skip": skip,
                    "limit": self.page_size,
                    "mode": "json",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            payload = response.json()

            if not isinstance(payload, list):
                raise TypeError("Lever postings must be a list.")

            for item in payload:
                if not isinstance(item, dict):
                    raise TypeError("Lever posting must be an object.")

                yield self._parse_job(item)

            if len(payload) < self.page_size:
                break

            skip += self.page_size

    def _parse_job(self, item: dict) -> Job:
        categories = item.get("categories") or {}

        if not isinstance(categories, dict):
            raise TypeError("Lever posting categories must be an object.")

        location = categories.get("location") or ""

        commitment = categories.get("commitment")
        employment_type = (
            str(commitment).strip()
            if commitment is not None
            else None
        )

        description = item.get("descriptionPlain") or ""

        return Job(
            title=str(item.get("text") or "").strip(),
            company=self.company_name,
            location=str(location).strip(),
            description=str(description),
            source=self.name,
            source_job_id=str(item["id"]),
            source_url=item["hostedUrl"],
            employment_type=employment_type,
            experience_required=None,
            skills=[],
            posted_at=None,
            discovered_at=datetime.now().astimezone(),
        )
