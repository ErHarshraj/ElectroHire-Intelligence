"""
Startup discovery domain and orchestration.

This module deliberately keeps source-specific HTTP/RSS logic out of the
discovery service. Sources produce normalized discovery items, while this
service handles orchestration and URL-level deduplication.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StartupNewsItem:
    """Normalized evidence item discovered from a startup/news source."""

    title: str
    summary: str | None
    url: str
    published_at: datetime | None
    source_name: str
    query: str


class StartupDiscoverySource(ABC):
    """Abstract interface for startup discovery sources."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique source name."""
        raise NotImplementedError

    @abstractmethod
    def discover(self) -> list[StartupNewsItem]:
        """Discover startup-related evidence items."""
        raise NotImplementedError


class StartupDiscoveryService:
    """Coordinate startup discovery and source-level deduplication."""

    def __init__(self, source: StartupDiscoverySource) -> None:
        self.source = source

    def discover(self) -> list[StartupNewsItem]:
        """Return unique discovery items from the configured source."""
        items = self.source.discover()

        unique_items: list[StartupNewsItem] = []
        seen_urls: set[str] = set()

        for item in items:
            if item.url in seen_urls:
                continue

            seen_urls.add(item.url)
            unique_items.append(item)

        return unique_items
