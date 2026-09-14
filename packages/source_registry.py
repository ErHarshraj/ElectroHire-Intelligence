"""
Registry for ElectroHire source adapters.

The registry stores common SourceAdapter implementations without
coupling specialized source contracts such as JobSource and
StartupDiscoverySource to each other.
"""

from __future__ import annotations

from packages.sources import SourceAdapter, SourceType


class SourceRegistry:
    """Store and retrieve registered source adapters."""

    def __init__(self) -> None:
        self._sources: dict[str, SourceAdapter] = {}

    def register(self, source: SourceAdapter) -> None:
        """Register a source adapter by its stable name."""
        if source.name in self._sources:
            raise ValueError(
                f"Source is already registered: {source.name!r}"
            )

        self._sources[source.name] = source

    def get(self, name: str) -> SourceAdapter:
        """Return a registered source by name."""
        return self._sources[name]

    def list(
        self,
        source_type: SourceType | None = None,
    ) -> list[SourceAdapter]:
        """Return registered sources, optionally filtered by type."""
        sources = list(self._sources.values())

        if source_type is None:
            return sources

        return [
            source
            for source in sources
            if source.source_type == source_type
        ]
