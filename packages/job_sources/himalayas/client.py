from typing import Any

import httpx


class HimalayasClient:
    """HTTP client for the public Himalayas jobs API."""

    BASE_URL = "https://himalayas.app/jobs/api"

    def __init__(
        self,
        timeout: float = 10.0,
    ) -> None:
        self.timeout = timeout

    def search_jobs(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """Fetch one page of jobs from Himalayas."""

        params: dict[str, str | int] = {
            "limit": limit,
        }

        if cursor:
            params["cursor"] = cursor

        response = httpx.get(
            self.BASE_URL,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise TypeError(
                "Himalayas API response must be a JSON object."
            )

        return data
