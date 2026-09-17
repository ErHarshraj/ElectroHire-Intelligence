"""
SmartRecruiters public career-board job source.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.sources import SourceAdapter, SourceType

SMARTRECRUITERS_POSTINGS_URL = (
    "https://api.smartrecruiters.com/v1/companies/"
)


class SmartRecruitersJobSource(JobSource, SourceAdapter):
    """
    Fetch active public jobs from a SmartRecruiters career board.
    """

    def __init__(
        self,
        *,
        company_name: str,
        company_identifier: str,
        opener: Callable[..., object] | None = None,
    ) -> None:
        self.company_name = company_name
        self.company_identifier = company_identifier
        self._opener = opener or urlopen

    @property
    def name(self) -> str:
        return f"smartrecruiters:{self.company_identifier}"

    @property
    def source_type(self) -> SourceType:
        return SourceType.JOB

    def fetch_jobs(self) -> list[Job]:
        """
        Fetch all active public SmartRecruiters postings.
        """

        postings = self._fetch_postings()

        jobs: list[Job] = []

        for posting in postings:
            if not isinstance(posting, dict):
                continue

            posting_id = (
                self._clean_text(posting.get("id"))
                or self._clean_text(posting.get("uuid"))
            )

            if not posting_id:
                continue

            details = self._fetch_posting_details(posting_id)

            if not isinstance(details, dict):
                continue

            if details.get("active") is False:
                continue

            job = self._parse_job(details)

            if job is not None:
                jobs.append(job)

        return jobs

    def _fetch_postings(self) -> list[dict]:
        """
        Fetch all public postings using SmartRecruiters pagination.
        """

        postings: list[dict] = []
        limit = 100
        offset = 0

        while True:
            payload = self._request_json(
                self._build_postings_url(
                    limit=limit,
                    offset=offset,
                )
            )

            content = payload.get("content", [])

            if not isinstance(content, list):
                raise ValueError(
                    "SmartRecruiters API returned invalid posting content."
                )

            page_postings = [
                item
                for item in content
                if isinstance(item, dict)
            ]

            postings.extend(page_postings)

            total_found = payload.get("totalFound")

            if not isinstance(total_found, int):
                total_found = len(postings)

            if not page_postings:
                break

            if len(postings) >= total_found:
                break

            offset += limit

        return postings

    def _fetch_posting_details(
        self,
        posting_id: str,
    ) -> dict:
        """
        Fetch complete details for one posting.
        """

        url = (
            f"{SMARTRECRUITERS_POSTINGS_URL}"
            f"{self.company_identifier}"
            f"/postings/{posting_id}"
        )

        return self._request_json(url)

    def _build_postings_url(
        self,
        *,
        limit: int,
        offset: int,
    ) -> str:
        base_url = (
            f"{SMARTRECRUITERS_POSTINGS_URL}"
            f"{self.company_identifier}"
            "/postings"
        )

        query = urlencode(
            {
                "limit": limit,
                "offset": offset,
                "destination": "PUBLIC",
            }
        )

        return f"{base_url}?{query}"

    def _request_json(self, url: str) -> dict:
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
                "SmartRecruiters API returned an unexpected response."
            )

        return payload

    def _parse_job(self, item: dict) -> Job | None:
        title = self._clean_text(item.get("name"))

        source_url = (
            self._clean_text(item.get("postingUrl"))
            or self._clean_text(item.get("applyUrl"))
        )

        if not title or not source_url:
            return None

        source_job_id = (
            self._clean_text(item.get("uuid"))
            or self._clean_text(item.get("id"))
        )

        if not source_job_id:
            return None

        description = self._build_description(item)

        location = self._build_location(item)

        employment_type = self._extract_label(
            item.get("typeOfEmployment")
        )

        experience_required = self._extract_label(
            item.get("experienceLevel")
        )

        posted_at = self._parse_datetime(
            item.get("releasedDate")
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
            source="smartrecruiters",
            source_job_id=source_job_id,
            source_url=source_url,
            employment_type=employment_type,
            experience_required=experience_required,
            skills=skills,
            posted_at=posted_at,
            discovered_at=datetime.now(),
        )

    @staticmethod
    def _build_description(
        item: dict,
    ) -> str | None:
        job_ad = item.get("jobAd")

        if not isinstance(job_ad, dict):
            return None

        sections = job_ad.get("sections")

        if not isinstance(sections, dict):
            return None

        parts: list[str] = []

        for section_name in (
            "companyDescription",
            "jobDescription",
            "qualifications",
            "additionalInformation",
        ):
            section = sections.get(section_name)

            if not isinstance(section, dict):
                continue

            text = SmartRecruitersJobSource._clean_text(
                section.get("text")
            )

            if text:
                parts.append(text)

        if not parts:
            return None

        return "\n\n".join(parts)

    @staticmethod
    def _build_location(
        item: dict,
    ) -> str | None:
        location = item.get("location")

        if not isinstance(location, dict):
            return None

        parts: list[str] = []

        city = SmartRecruitersJobSource._clean_text(
            location.get("city")
        )
        region = SmartRecruitersJobSource._clean_text(
            location.get("region")
        )
        country = SmartRecruitersJobSource._clean_text(
            location.get("country")
        )

        if city:
            parts.append(city)

        if region:
            parts.append(region)

        if country:
            parts.append(country)

        remote = location.get("remote")

        if remote is True:
            parts.append("Remote")

        if not parts:
            return None

        return ", ".join(parts)

    @staticmethod
    def _extract_label(
        value: object,
    ) -> str | None:
        if not isinstance(value, dict):
            return None

        return SmartRecruitersJobSource._clean_text(
            value.get("label")
        )

    @staticmethod
    def _clean_text(
        value: object,
    ) -> str | None:
        if not isinstance(value, str):
            return None

        value = value.strip()

        return value or None

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
        Extract obvious electronics/engineering keywords.

        The existing relevance engine remains responsible
        for actual skill interpretation.
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
