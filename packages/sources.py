"""
Common source-adapter contract for ElectroHire.

A source adapter represents an external discovery provider.

Specialized source contracts such as JobSource and
StartupDiscoverySource remain independent because they return
different domain objects.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum


class SourceType(str, Enum):
    """Supported categories of external discovery sources."""

    JOB = "job"
    STARTUP = "startup"
    COMPANY = "company"


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
    def source_type(self) -> SourceType:
        """Return the type of discovery source."""
        raise NotImplementedError
