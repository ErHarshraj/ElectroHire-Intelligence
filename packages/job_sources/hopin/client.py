from typing import Any

import httpx


class HopinClient:
    """HTTP client for the public Hopin jobs API."""

    BASE_URL = "https://api.hopinjobs.com/api"

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch_jobs(
        self,
        *,
        industry: str | None = None,
        location: str | None = None,
        work_type: str | None = None,
        role_type: str | None = None,
        unofficial: bool = False,
    ) -> list[dict[str, Any]]:
        """Fetch filtered Hopin job listings."""

        return self._fetch_collection(
            endpoint="jobs",
            response_key="jobs",
            industry=industry,
            location=location,
            work_type=work_type,
            role_type=role_type,
            unofficial=unofficial,
        )

    def fetch_internships(
        self,
        *,
        industry: str | None = None,
        location: str | None = None,
        work_type: str | None = None,
        role_type: str | None = None,
        unofficial: bool = False,
    ) -> list[dict[str, Any]]:
        """Fetch filtered Hopin internship listings."""

        return self._fetch_collection(
            endpoint="internships",
            response_key="internships",
            industry=industry,
            location=location,
            work_type=work_type,
            role_type=role_type,
            unofficial=unofficial,
        )

    def _fetch_collection(
        self,
        *,
        endpoint: str,
        response_key: str,
        industry: str | None,
        location: str | None,
        work_type: str | None,
        role_type: str | None,
        unofficial: bool,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {
            "is_unofficial": str(unofficial).lower(),
        }

        if industry:
            params["industry"] = industry

        if location:
            params["location"] = location

        if work_type:
            params["work_type"] = work_type

        if role_type:
            params["role_type"] = role_type

        response = httpx.get(
            f"{self.BASE_URL}/{endpoint}",
            params=params,
            timeout=self.timeout,
            headers={"User-Agent": "ElectroHire Intelligence"},
        )
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise TypeError(
                f"Hopin {endpoint} API response must be a JSON object."
            )

        records = data.get(response_key)

        if not isinstance(records, list):
            raise TypeError(
                f"Hopin {endpoint} API response must contain "
                f"a {response_key} list."
            )

        return [
            item
            for item in records
            if isinstance(item, dict)
            and item.get("id")
            and item.get("title")
            and item.get("company")
        ]
