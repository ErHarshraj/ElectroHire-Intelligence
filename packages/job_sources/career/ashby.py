"""
Ashby public career-board job source.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime
from urllib.request import Request, urlopen

from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.sources import SourceAdapter, SourceType

ASHBY_POSTINGS_URL = (
    "https://api.ashbyhq.com/posting-api/job-board/"
)


class AshbyJobSource(JobSource, SourceAdapter):
    """
    Fetch published jobs from an Ashby public job board.
    """

    def __init__(
        self,
        *,
        company_name: str,
        board_name: str,
        opener: Callable[..., object] | None = None,
    ) -> None:
        self.company_name = company_name
        self.board_name = board_name
        self._opener = opener or urlopen

    @property
    def name(self) -> str:
        return f"ashby:{self.board_name}"

    @property
    def source_type(self) -> SourceType:
        return SourceType.JOB

    def fetch_jobs(self) -> list[Job]:
        """Fetch and convert all published Ashby postings."""

        payload = self._fetch_payload()

        jobs: list[Job] = []

        for item in payload.get("jobs", []):
            if not isinstance(item, dict):
                continue

            if item.get("isListed") is False:
                continue

            job = self._parse_job(item)

            if job is not None:
                jobs.append(job)

        return jobs

    def _fetch_payload(self) -> dict:
        url = (
            f"{ASHBY_POSTINGS_URL}"
            f"{self.board_name}"
            "?includeCompensation=false"
        )

        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "ElectroHire-Intelligence/0.1",
            },
            method="GET",
        )

        with self._opener(request, timeout=20) as response:
            raw = response.read()

        payload = json.loads(raw)

        if not isinstance(payload, dict):
            raise ValueError(
                "Ashby API returned an unexpected response."
            )

        return payload

    def _parse_job(self, item: dict) -> Job | None:
        title = self._clean_text(item.get("title"))

        job_url = (
            self._clean_text(item.get("jobUrl"))
            or self._clean_text(item.get("applyUrl"))
        )

        if not title or not job_url:
            return None

        source_job_id = self._build_source_job_id(job_url)

        location = self._build_location(item)

        description = (
            self._clean_text(item.get("descriptionPlain"))
            or self._clean_text(item.get("descriptionHtml"))
        )

        employment_type = self._clean_text(
            item.get("employmentType")
        )

        posted_at = self._parse_datetime(
            item.get("publishedAt")
        )

        skills = self._extract_skills(
            title=title,
            description=description,
        )

        return Job(
            title=title,
            company=self.company_name,
            location=location,
            description=description,
            source="ashby",
            source_job_id=source_job_id,
            source_url=job_url,
            employment_type=employment_type,
            experience_required=None,
            skills=skills,
            posted_at=posted_at,
            discovered_at=datetime.now(),
        )

    @staticmethod
    def _clean_text(value: object) -> str | None:
        if not isinstance(value, str):
            return None

        value = value.strip()

        return value or None

    @staticmethod
    def _build_source_job_id(job_url: str) -> str:
        """
        Generate a deterministic identifier from the public posting URL.
        """

        return hashlib.sha256(
            job_url.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _build_location(item: dict) -> str | None:
        location = AshbyJobSource._clean_text(
            item.get("location")
        )

        secondary_locations = item.get(
            "secondaryLocations"
        )

        values: list[str] = []

        if location:
            values.append(location)

        if isinstance(secondary_locations, list):
            for value in secondary_locations:
                cleaned = AshbyJobSource._clean_text(value)

                if cleaned and cleaned not in values:
                    values.append(cleaned)

        if not values:
            address = item.get("address")

            if isinstance(address, dict):
                postal = address.get("postalAddress")

                if isinstance(postal, dict):
                    locality = AshbyJobSource._clean_text(
                        postal.get("addressLocality")
                    )
                    region = AshbyJobSource._clean_text(
                        postal.get("addressRegion")
                    )
                    country = AshbyJobSource._clean_text(
                        postal.get("addressCountry")
                    )

                    parts = [
                        part
                        for part in (locality, region, country)
                        if part
                    ]

                    if parts:
                        values.append(", ".join(parts))

        if not values:
            return None

        return "; ".join(values)

    @staticmethod
    def _parse_datetime(
        value: object,
    ) -> datetime | None:
        if not isinstance(value, str) or not value.strip():
            return None

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError:
            return None

    @staticmethod
    def _extract_skills(
        *,
        title: str,
        description: str | None,
    ) -> list[str]:
        """
        Extract only obvious electronics/engineering keywords.

        This is intentionally lightweight. The existing relevance
        engine remains responsible for actual skill interpretation.
        """

        text = f"{title} {description or ''}".lower()

        keywords = [
            "embedded",
            "firmware",
            "electronics",
            "hardware",
            "pcb",
            "altium",
            "kicad",
            "circuit",
            "microcontroller",
            "microprocessor",
            "fpga",
            "verilog",
            "vhdl",
            "iot",
            "robotics",
            "power electronics",
            "ltspice",
            "spi",
            "i2c",
            "uart",
            "can",
            "rtos",
            "esp32",
            "stm32",
            "arduino",
        ]

        return [
            keyword
            for keyword in keywords
            if keyword in text
        ]
