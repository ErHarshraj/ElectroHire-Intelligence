from typing import Any

import httpx


class FourDayWeekClient:
    """HTTP client for the public 4dayweek.io jobs API."""

    BASE_URL = "https://4dayweek.io/api/v2/jobs"

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch_jobs(self, *, limit: int = 100) -> list[dict[str, Any]]:
        """Fetch all public 4dayweek.io jobs through pagination."""
        if not 1 <= limit <= 100:
            raise ValueError(
                "4dayweek limit must be between 1 and 100."
            )

        jobs: list[dict[str, Any]] = []
        page = 1

        while True:
            response = httpx.get(
                self.BASE_URL,
                params={"page": page, "limit": limit},
                timeout=self.timeout,
                headers={"User-Agent": "ElectroHire Intelligence"},
            )
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, dict):
                raise TypeError(
                    "4dayweek API response must be a JSON object."
                )

            page_jobs = data.get("data")

            if not isinstance(page_jobs, list):
                raise TypeError(
                    "4dayweek API response must contain a data list."
                )

            jobs.extend(
                item
                for item in page_jobs
                if isinstance(item, dict)
                and "id" in item
                and "title" in item
            )

            has_more = data.get("has_more")

            if not isinstance(has_more, bool):
                raise TypeError(
                    "4dayweek API response must contain a boolean has_more."
                )

            if not has_more:
                break

            page += 1

        return jobs
