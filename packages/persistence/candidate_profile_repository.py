from abc import ABC, abstractmethod

from packages.domain.candidate_profile import CandidateProfile


class CandidateProfileRepository(ABC):
    """Persistence interface for the canonical candidate profile."""

    @abstractmethod
    def get(self) -> CandidateProfile | None:
        """Return the persisted candidate profile, if one exists."""
        raise NotImplementedError

    @abstractmethod
    def save(self, profile: CandidateProfile) -> int:
        """Create or replace the canonical candidate profile."""
        raise NotImplementedError
