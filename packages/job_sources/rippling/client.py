from __future__ import annotations

from typing import Any

import httpx


class RipplingClient:
    """HTTP client for public Rippling career boards."""

    BASE_API_URL = "https://api.rippling.com/platform/api/ats/v1/board"
    BASE_JOB_URL = "https://ats.rippling.com"

    def __init__(
        self,
        *,
        board_slug: str,
        timeout: float = 15.0,
    ) -> None:
        if not board_slug.strip():
            raise ValueError("Rippling board slug must not be empty.")

        self.board_slug = board_slug.strip()
        self.timeout = timeout

    @property
    def board_url(self) -> str:
        """Return the public Rippling board jobs endpoint."""
        return f"{self.BASE_API_URL}/{self.board_slug}/jobs"

    def job_url(self, job_uuid: str) -> str:
        """Return the public Rippling job detail URL."""
        job_uuid = job_uuid.strip()

        if not job_uuid:
            raise ValueError("Rippling job UUID must not be empty.")

        return f"{self.BASE_JOB_URL}/{self.board_slug}/jobs/{job_uuid}"

    def fetch_board_jobs(self) -> list[dict[str, Any]]:
        """Fetch jobs exposed by the configured Rippling board."""
        response = httpx.get(
            self.board_url,
            timeout=self.timeout,
            headers={
                "User-Agent": "ElectroHire Intelligence",
            },
        )
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list):
            raise TypeError("Rippling board response must be a JSON array.")

        return [job for job in data if isinstance(job, dict) and job.get("uuid")]

    def fetch_job_detail(self, job_uuid: str) -> dict[str, Any]:
        """Fetch and extract the structured job payload from a job page."""
        response = httpx.get(
            self.job_url(job_uuid),
            timeout=self.timeout,
            headers={
                "User-Agent": "ElectroHire Intelligence",
            },
        )
        response.raise_for_status()

        html = response.text

        next_data = _extract_next_data(html)

        page_props = next_data.get("props", {}).get("pageProps")

        if not isinstance(page_props, dict):
            raise TypeError("Rippling job page is missing pageProps.")

        api_data = page_props.get("apiData")

        if not isinstance(api_data, dict):
            raise TypeError("Rippling job page is missing apiData.")

        job_post = api_data.get("jobPost")

        if not isinstance(job_post, dict):
            raise TypeError("Rippling job page is missing jobPost.")

        return api_data


def _extract_next_data(html: str) -> dict[str, Any]:
    """Extract the __NEXT_DATA__ JSON object from a Rippling page."""
    marker = '<script id="__NEXT_DATA__" type="application/json">'

    start = html.find(marker)

    if start == -1:
        raise ValueError("Rippling job page does not contain __NEXT_DATA__.")

    start += len(marker)

    end = html.find("</script>", start)

    if end == -1:
        raise ValueError("Rippling __NEXT_DATA__ script is not closed.")

    payload = html[start:end].strip()

    if not payload:
        raise ValueError("Rippling __NEXT_DATA__ payload is empty.")

    import json

    data = json.loads(payload)

    if not isinstance(data, dict):
        raise TypeError("Rippling __NEXT_DATA__ must contain a JSON object.")

    return data
