from __future__ import annotations

from typing import Any
from xml.etree import ElementTree

import httpx


class StartupJobsClient:
    """HTTP client for the public Startup Jobs RSS feeds."""

    BASE_URL = "https://startup.jobs/feeds/jobs"

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def fetch_jobs(
        self,
        *,
        role: str,
    ) -> list[dict[str, Any]]:
        """Fetch jobs from a Startup Jobs role RSS feed."""

        role = role.strip()

        if not role:
            raise ValueError("Startup Jobs role must not be empty.")

        response = httpx.get(
            self.BASE_URL,
            params={"role": role},
            timeout=self.timeout,
            headers={
                "User-Agent": "ElectroHire Intelligence",
                "Accept": "application/rss+xml, application/xml, text/xml",
            },
        )
        response.raise_for_status()

        try:
            root = ElementTree.fromstring(response.content)
        except ElementTree.ParseError as exc:
            raise ValueError(
                "Startup Jobs RSS response is not valid XML."
            ) from exc

        items: list[dict[str, Any]] = []

        for item in root.findall(".//item"):
            parsed: dict[str, Any] = {}

            for child in item:
                tag = child.tag

                if not isinstance(tag, str):
                    continue

                if tag == "category":
                    parsed.setdefault("categories", []).append(
                        child.text or ""
                    )
                    continue

                parsed[tag] = child.text or ""

            if parsed.get("title") and parsed.get("guid"):
                items.append(parsed)

        return items
