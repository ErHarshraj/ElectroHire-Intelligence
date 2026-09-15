"""
Common contract for public company career-site job sources.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from packages.domain.job import Job
from packages.job_sources.base import JobSource
from packages.sources import SourceAdapter


class CareerSiteJobSource(JobSource, SourceAdapter, ABC):
    """
    Common interface for public company career-site / ATS sources.

    A concrete adapter is responsible only for:
    - fetching public postings
    - converting them into ElectroHire Job objects

    All downstream intelligence remains unchanged.
    """

    @property
    @abstractmethod
    def company_name(self) -> str:
        """Return the company represented by this career source."""
        raise NotImplementedError

    @abstractmethod
    def fetch_jobs(self) -> Iterable[Job]:
        """Fetch published jobs from the public career source."""
        raise NotImplementedError
