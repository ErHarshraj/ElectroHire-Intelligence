from abc import ABC, abstractmethod
from collections.abc import Iterable

from packages.domain.job import Job


class JobSource(ABC):
    """Abstract interface for a job opportunity source."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique source name."""
        raise NotImplementedError

    @abstractmethod
    def fetch_jobs(self) -> Iterable[Job]:
        """Fetch jobs from the source."""
        raise NotImplementedError
