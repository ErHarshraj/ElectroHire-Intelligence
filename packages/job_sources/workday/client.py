from __future__ import annotations

from typing import Any

import httpx


class WorkdayClient:
    """HTTP client for public Workday CXS career boards."""

    PAGE_SIZE = 20

    def __init__(
        self,
        *,
        base_url: str,
        tenant: str,
        site: str,
        timeout: float = 15.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.tenant = tenant
        self.site = site
        self.timeout = timeout

    @property
    def jobs_url(self) -> str:
        """Return the Workday CXS job-list endpoint."""
        return (
            f"{self.base_url}/wday/cxs/"
            f"{self.tenant}/{self.site}/jobs"
        )

    def fetch_jobs(
        self,
        *,
        batches: int = 1,
    ) -> list[dict[str, Any]]:
        """Fetch compact job records using Workday offset pagination."""
        if not 1 <= batches <= 100:
            raise ValueError(
                "Workday batch count must be between 1 and 100."
            )

        jobs: list[dict[str, Any]] = []

        for batch_number in range(batches):
            offset = batch_number * self.PAGE_SIZE

            response = httpx.post(
                self.jobs_url,
                json={
                    "appliedFacets": {},
                    "limit": self.PAGE_SIZE,
                    "offset": offset,
                    "searchText": "",
                },
                timeout=self.timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "ElectroHire Intelligence",
                },
            )
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, dict):
                raise TypeError(
                    "Workday API response must be a JSON object."
                )

            page_jobs = data.get("jobPostings")

            if not isinstance(page_jobs, list):
                raise TypeError(
                    "Workday API response must contain "
                    "a jobPostings list."
                )

            if not page_jobs:
                break

            jobs.extend(
                item
                for item in page_jobs
                if isinstance(item, dict)
                and item.get("title")
                and item.get("externalPath")
            )

        return jobs

    def fetch_job_detail(
        self,
        *,
        external_path: str,
    ) -> dict[str, Any]:
        """Fetch the complete Workday job posting."""
        if not external_path.startswith("/"):
            raise ValueError(
                "Workday externalPath must start with '/'."
            )

        url = f"{self.base_url}/wday/cxs/{self.tenant}/{self.site}{external_path}"

        response = httpx.get(
            url,
            timeout=self.timeout,
            headers={
                "User-Agent": "ElectroHire Intelligence",
            },
        )
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise TypeError(
                "Workday job detail response must be a JSON object."
            )

        job_posting_info = data.get("jobPostingInfo")

        if not isinstance(job_posting_info, dict):
            raise TypeError(
                "Workday job detail response must contain "
                "a jobPostingInfo object."
            )

        return job_posting_info
