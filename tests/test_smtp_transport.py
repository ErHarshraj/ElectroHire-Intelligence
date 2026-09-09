from email.message import EmailMessage
from unittest.mock import MagicMock, patch

import pytest

from packages.application.email.smtp import SMTPEmailTransport


def make_message() -> EmailMessage:
    message = EmailMessage()
    message["From"] = "sender@example.com"
    message["To"] = "recipient@example.com"
    message["Subject"] = "Test"
    message.set_content("Test message")
    return message


def make_smtp_mock() -> MagicMock:
    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    return smtp


def test_smtp_transport_sends_message() -> None:
    smtp = make_smtp_mock()

    with patch(
        "packages.application.email.smtp.smtplib.SMTP",
        return_value=smtp,
    ) as smtp_class:
        transport = SMTPEmailTransport(
            host="smtp.example.com",
            port=587,
            username="sender@example.com",
            password="secret",
        )

        message = make_message()
        transport.send(message)

    smtp_class.assert_called_once_with(
        "smtp.example.com",
        587,
        timeout=30.0,
    )
    assert smtp.ehlo.call_count == 2
    smtp.starttls.assert_called_once_with()
    smtp.login.assert_called_once_with(
        "sender@example.com",
        "secret",
    )
    smtp.send_message.assert_called_once_with(message)
    smtp.__exit__.assert_called_once()


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        (
            {
                "host": "",
                "port": 587,
                "username": "sender@example.com",
                "password": "secret",
            },
            "SMTP host is required",
        ),
        (
            {
                "host": "smtp.example.com",
                "port": 0,
                "username": "sender@example.com",
                "password": "secret",
            },
            "SMTP port must be between 1 and 65535",
        ),
        (
            {
                "host": "smtp.example.com",
                "port": 587,
                "username": "",
                "password": "secret",
            },
            "SMTP username is required",
        ),
        (
            {
                "host": "smtp.example.com",
                "port": 587,
                "username": "sender@example.com",
                "password": "",
            },
            "SMTP password is required",
        ),
        (
            {
                "host": "smtp.example.com",
                "port": 587,
                "username": "sender@example.com",
                "password": "secret",
                "timeout": 0,
            },
            "SMTP timeout must be greater than zero",
        ),
    ],
)
def test_smtp_transport_validates_configuration(
    kwargs: dict[str, object],
    expected: str,
) -> None:
    with pytest.raises(ValueError, match=expected):
        SMTPEmailTransport(**kwargs)  # type: ignore[arg-type]


def test_smtp_transport_propagates_smtp_error() -> None:
    smtp = make_smtp_mock()
    smtp.login.side_effect = RuntimeError("authentication failed")

    with patch(
        "packages.application.email.smtp.smtplib.SMTP",
        return_value=smtp,
    ):
        transport = SMTPEmailTransport(
            host="smtp.example.com",
            port=587,
            username="sender@example.com",
            password="secret",
        )

        with pytest.raises(RuntimeError, match="authentication failed"):
            transport.send(make_message())
