"""
Google News RSS startup discovery source.

Google News provides public RSS search feeds. This adapter only retrieves
and normalizes article evidence. It does not attempt to infer company
identity from article text.
"""

from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote
from xml.etree import ElementTree

import httpx

from packages.opportunity.discovery import (
    StartupDiscoverySource,
    StartupNewsItem,
)
from packages.sources import SourceAdapter, SourceType


class GoogleNewsStartupSource(StartupDiscoverySource, SourceAdapter):
    """Discover startup-related news through a Google News RSS search."""

    name = "google_news"

    BASE_URL = "https://news.google.com/rss/search"

    @property
    def source_type(self) -> SourceType:
        return SourceType.STARTUP

    def __init__(
        self,
        query: str = (
            'India startup '
            '(hardware OR electronics OR embedded OR robotics OR '
            'semiconductor OR "deep tech")'
        ),
        *,
        language: str = "en-IN",
        country: str = "IN",
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        if not query.strip():
            raise ValueError("Google News query must not be empty.")

        if not language.strip():
            raise ValueError("Google News language must not be empty.")

        if not country.strip():
            raise ValueError("Google News country must not be empty.")

        if timeout <= 0:
            raise ValueError("Google News timeout must be greater than zero.")

        self.query = query
        self.language = language
        self.country = country
        self.timeout = timeout
        self.client = client

    def _build_url(self) -> str:
        """Build the public Google News RSS search URL."""
        encoded_query = quote(self.query)

        return (
            f"{self.BASE_URL}"
            f"?q={encoded_query}"
            f"&hl={self.language}"
            f"&gl={self.country}"
            f"&ceid={self.country}:{self.language.split('-')[0]}"
        )

    def _fetch(self) -> str:
        """Fetch the RSS document."""
        if self.client is not None:
            response = self.client.get(
                self._build_url(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.text

        with httpx.Client() as client:
            response = client.get(
                self._build_url(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.text

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        """Parse an RSS publication date."""
        if not value:
            return None

        try:
            return parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _parse_items(
        cls,
        xml_text: str,
        *,
        query: str,
    ) -> list[StartupNewsItem]:
        """Parse RSS items into normalized discovery records."""
        try:
            root = ElementTree.fromstring(xml_text)
        except ElementTree.ParseError as exc:
            raise ValueError("Google News RSS response is invalid XML.") from exc

        items: list[StartupNewsItem] = []

        for item in root.findall("./channel/item"):
            title = (item.findtext("title") or "").strip()
            url = (item.findtext("link") or "").strip()
            summary = (item.findtext("description") or "").strip() or None
            published_raw = item.findtext("pubDate")
            source_name = (
                item.findtext("source")
                or "Google News"
            ).strip()

            if not title or not url:
                continue

            items.append(
                StartupNewsItem(
                    title=title,
                    summary=summary,
                    url=url,
                    published_at=cls._parse_datetime(published_raw),
                    source_name=source_name,
                    query=query,
                )
            )

        return items

    def discover(self) -> list[StartupNewsItem]:
        """Fetch and parse startup-related Google News results."""
        xml_text = self._fetch()

        return self._parse_items(
            xml_text,
            query=self.query,
        )
