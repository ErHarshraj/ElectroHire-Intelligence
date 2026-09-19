from typing import Any

import httpx


class RemoteOKClient:
    """HTTP client for the public Remote OK jobs API."""

    BASE_URL = "https://remoteok.com/api"

    def __init__(
        self,
        timeout: float = 10.0,
    ) -> None:
        self.timeout = timeout

    def fetch_jobs(self) -> list[dict[str, Any]]:
        """Fetch the public Remote OK job feed."""

        response = httpx.get(
            self.BASE_URL,
            timeout=self.timeout,
            headers={
                "User-Agent": "ElectroHire Intelligence",
            },
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list):
            raise TypeError(
                "Remote OK API response must be a JSON array."
            )

        jobs: list[dict[str, Any]] = []

        for item in data:
            if not isinstance(item, dict):
                continue

            # The first array element is API metadata rather than a job.
            if "id" not in item or "position" not in item:
                continue

            jobs.append(item)

        return jobs
