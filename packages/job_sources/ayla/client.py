from typing import Any

import httpx


class AylaClient:
    """HTTP client for the public AylaGov jobs API."""

    BASE_URL = "https://aylagov.com/api/jobs/search"

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch_jobs(
        self,
        *,
        query: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Fetch all AylaGov jobs matching a search query."""
        query = query.strip()

        if not query:
            raise ValueError("Ayla query must not be empty.")

        if not 1 <= limit <= 100:
            raise ValueError(
                "Ayla limit must be between 1 and 100."
            )

        jobs: list[dict[str, Any]] = []
        page = 0

        while True:
            response = httpx.get(
                self.BASE_URL,
                params={
                    "search": query,
                    "limit": limit,
                    "page": page,
                },
                timeout=self.timeout,
                headers={"User-Agent": "ElectroHire Intelligence"},
            )
            response.raise_for_status()

            data = response.json()

            if not isinstance(data, dict):
                raise TypeError(
                    "Ayla API response must be a JSON object."
                )

            page_jobs = data.get("jobs")

            if not isinstance(page_jobs, list):
                raise TypeError(
                    "Ayla API response must contain a jobs list."
                )

            jobs.extend(
                item
                for item in page_jobs
                if isinstance(item, dict)
                and "id" in item
                and "title" in item
            )

            pagination = data.get("pagination")

            if not isinstance(pagination, dict):
                raise TypeError(
                    "Ayla API response must contain "
                    "pagination metadata."
                )

            total = pagination.get("total")
            current_offset = pagination.get("offset")

            if not isinstance(total, int):
                raise TypeError(
                    "Ayla pagination must contain an integer total."
                )

            if not isinstance(current_offset, int):
                raise TypeError(
                    "Ayla pagination must contain an integer offset."
                )

            if not page_jobs:
                break

            if current_offset + len(page_jobs) >= total:
                break

            page += 1

        return jobs
