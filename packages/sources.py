"""
Common source-adapter contract for ElectroHire.

A source adapter represents an external discovery provider.

Specialized source contracts such as JobSource and
StartupDiscoverySource remain independent because they return
different domain objects.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class SourceAdapter(ABC):
    """
    Common metadata contract shared by all external sources.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable source name."""
        raise NotImplementedError

    @property
    @abstractmethod
    def source_type(self) -> str:
        """
        Return the type of discovery source.

        Examples:
        - job
        - startup
        - company
        """
        raise NotImplementedError
