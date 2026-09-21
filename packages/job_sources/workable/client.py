from __future__ import annotations

from typing import Any

import httpx


class WorkableClient:
    """HTTP client for public Workable career accounts."""

    def __init__(
        self,
        *,
        account_slug: str,
        timeout: float = 15.0,
    ) -> None:
        if not account_slug.strip():
            raise ValueError("Workable account slug must not be empty.")

        self.account_slug = account_slug.strip()
        self.timeout = timeout

    @property
    def jobs_url(self) -> str:
        """Return the public Workable jobs endpoint."""
        return (
            "https://apply.workable.com/api/v1/widget/accounts/"
            f"{self.account_slug}?details=true"
        )

    def fetch_jobs(self) -> list[dict[str, Any]]:
        """Fetch all publicly exposed jobs for the configured account."""
        response = httpx.get(
            self.jobs_url,
            timeout=self.timeout,
            headers={
                "User-Agent": "ElectroHire Intelligence",
            },
        )
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise TypeError(
                "Workable API response must be a JSON object."
            )

        jobs = data.get("jobs")

        if not isinstance(jobs, list):
            raise TypeError(
                "Workable API response must contain a jobs list."
            )

        return [
            job
            for job in jobs
            if isinstance(job, dict)
            and job.get("title")
            and job.get("shortcode")
            and job.get("url")
        ]
