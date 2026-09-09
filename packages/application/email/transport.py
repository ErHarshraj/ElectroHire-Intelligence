from abc import ABC, abstractmethod
from email.message import EmailMessage


class EmailTransport(ABC):
    """Transport boundary for sending email messages."""

    @abstractmethod
    def send(self, message: EmailMessage) -> None:
        """Send one email message."""
        raise NotImplementedError
