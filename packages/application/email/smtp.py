import smtplib
from email.message import EmailMessage

from packages.application.email.transport import EmailTransport


class SMTPEmailTransport(EmailTransport):
    """Send email messages through an SMTP server."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        *,
        timeout: float = 30.0,
    ) -> None:
        if not host.strip():
            raise ValueError("SMTP host is required")

        if port <= 0 or port > 65535:
            raise ValueError("SMTP port must be between 1 and 65535")

        if not username.strip():
            raise ValueError("SMTP username is required")

        if not password:
            raise ValueError("SMTP password is required")

        if timeout <= 0:
            raise ValueError("SMTP timeout must be greater than zero")

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout

    def send(self, message: EmailMessage) -> None:
        """Send one message using STARTTLS SMTP."""

        with smtplib.SMTP(
            self.host,
            self.port,
            timeout=self.timeout,
        ) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(self.username, self.password)
            smtp.send_message(message)
