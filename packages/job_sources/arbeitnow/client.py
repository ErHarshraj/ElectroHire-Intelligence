from typing import Any

import httpx


class ArbeitnowClient:
    """HTTP client for the public Arbeitnow job board API."""

    BASE_URL = "https://www.arbeitnow.com/api/job-board-api"

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch_jobs(self, *, pages: int = 1) -> list[dict[str, Any]]:
        """Fetch public Arbeitnow job listings across API pages."""
        if not 1 <= pages <= 20:
            raise ValueError(
                "Arbeitnow page count must be between 1 and 20."
            )

        jobs: list[dict[str, Any]] = []
        next_url: str | None = self.BASE_URL

        for _page_number in range(1, pages + 1):
            if not next_url:
                break

            response = httpx.get(
                next_url,
                timeout=self.timeout,
                headers={"User-Agent": "ElectroHire Intelligence"},
            )
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, dict):
                raise TypeError(
                    "Arbeitnow API response must be a JSON object."
                )

            page_jobs = data.get("data")

            if not isinstance(page_jobs, list):
                raise TypeError(
                    "Arbeitnow API response must contain a data list."
                )

            jobs.extend(
                item
                for item in page_jobs
                if isinstance(item, dict)
                and "slug" in item
                and "title" in item
            )

            links = data.get("links")

            if not isinstance(links, dict):
                next_url = None
                continue

            next_url_value = links.get("next")
            next_url = (
                str(next_url_value)
                if next_url_value
                else None
            )

        return jobs
