from typing import Any

import httpx


class JobicyClient:
    """HTTP client for the public Jobicy remote jobs API."""

    BASE_URL = "https://jobicy.com/api/v2/remote-jobs"

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch_jobs(self, *, count: int = 200) -> list[dict[str, Any]]:
        """Fetch public Jobicy remote job listings."""
        if not 1 <= count <= 200:
            raise ValueError("Jobicy count must be between 1 and 200.")

        response = httpx.get(
            self.BASE_URL,
            params={"count": count},
            timeout=self.timeout,
            headers={"User-Agent": "ElectroHire Intelligence"},
        )
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise TypeError("Jobicy API response must be a JSON object.")

        jobs = data.get("jobs")

        if not isinstance(jobs, list):
            raise TypeError("Jobicy API response must contain a jobs list.")

        return [
            item
            for item in jobs
            if isinstance(item, dict)
            and "id" in item
            and "jobTitle" in item
        ]
