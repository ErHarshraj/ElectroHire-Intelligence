from abc import ABC, abstractmethod

from packages.application.models import ApplicationRequest, ApplicationResult


class ApplicationAdapter(ABC):
    """Interface implemented by every application submission mechanism."""

    @abstractmethod
    def submit(self, request: ApplicationRequest) -> ApplicationResult:
        """Submit an application using the adapter's mechanism."""
        raise NotImplementedError
