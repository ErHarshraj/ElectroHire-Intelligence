"""
Factory registry for ElectroHire source adapters.

Factories create configured source-adapter instances. This keeps source
construction separate from source registration and allows one source
provider to have multiple configurations.
"""

from __future__ import annotations

from collections.abc import Callable

from packages.sources import SourceAdapter, SourceType

SourceFactory = Callable[..., SourceAdapter]


class SourceFactoryRegistry:
    """Store and retrieve source factories by stable source name."""

    def __init__(self) -> None:
        self._factories: dict[str, SourceFactory] = {}
        self._source_types: dict[str, SourceType] = {}

    def register(
        self,
        name: str,
        source_type: SourceType,
        factory: SourceFactory,
    ) -> None:
        """Register a source factory."""
        if not name.strip():
            raise ValueError("Source factory name must not be empty.")

        if name in self._factories:
            raise ValueError(
                f"Source factory is already registered: {name!r}"
            )

        self._factories[name] = factory
        self._source_types[name] = source_type

    def get(self, name: str) -> SourceFactory:
        """Return a registered factory by source name."""
        return self._factories[name]

    def source_type(self, name: str) -> SourceType:
        """Return the source type associated with a factory."""
        return self._source_types[name]

    def list(
        self,
        source_type: SourceType | None = None,
    ) -> list[str]:
        """Return registered factory names, optionally filtered by type."""
        names = list(self._factories)

        if source_type is None:
            return names

        return [
            name
            for name in names
            if self._source_types[name] == source_type
        ]
