from typing import Any

import httpx


class AdzunaClient:
    """HTTP client for the Adzuna job-search API."""

    BASE_URL = "https://api.adzuna.com/v1/api"

    def __init__(
        self,
        app_id: str,
        app_key: str,
        country: str = "in",
        timeout: float = 10.0,
    ) -> None:
        self.app_id = app_id
        self.app_key = app_key
        self.country = country
        self.timeout = timeout

    def search_jobs(
        self,
        query: str,
        page: int = 1,
        results_per_page: int = 20,
    ) -> dict[str, Any]:
        """Fetch one page of jobs from Adzuna."""

        url = (
            f"{self.BASE_URL}/jobs/"
            f"{self.country}/search/{page}"
        )

        params: dict[str, str | int] = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": query,
            "results_per_page": results_per_page,
        }

        response = httpx.get(
            url,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise TypeError("Adzuna API response must be a JSON object.")

        return data
