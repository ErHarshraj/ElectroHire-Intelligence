from email.message import EmailMessage
from pathlib import Path

from packages.application.adapters.email import EmailApplicationAdapter
from packages.application.email.builder import EmailBuilder
from packages.application.email.transport import EmailTransport
from packages.application.models import (
    ApplicationMethod,
    ApplicationRequest,
    ApplicationStatus,
)
from packages.application.profile import CandidateProfile


class FakeEmailTransport(EmailTransport):
    def __init__(self) -> None:
        self.messages: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> None:
        self.messages.append(message)


def make_candidate(resume_path: Path) -> CandidateProfile:
    return CandidateProfile(
        full_name="Harshraj",
        email="harshraj@example.com",
        phone="9876543210",
        location="India",
        resume_path=str(resume_path),
        linkedin_url="https://linkedin.com/in/harshraj",
        github_url="https://github.com/ErHarshraj",
    )


def make_request() -> ApplicationRequest:
    return ApplicationRequest(
        source="adzuna",
        source_job_id="12345",
        job_title="Hardware Design Engineer",
        company="Example Electronics",
        application_method=ApplicationMethod.EMAIL,
        recruiter_email="careers@example.com",
    )


def test_email_adapter_builds_and_sends_message(tmp_path: Path) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"fake pdf content")

    template = tmp_path / "template.txt"
    template.write_text(
        "Subject: Application for {{job_title}} at {{company}}\n\n"
        "Dear Hiring Manager,\n\n"
        "I am {{name}}.\n",
        encoding="utf-8",
    )

    transport = FakeEmailTransport()
    adapter = EmailApplicationAdapter(
        candidate=make_candidate(resume),
        builder=EmailBuilder(template),
        transport=transport,
    )

    result = adapter.submit(make_request())

    assert result.status == ApplicationStatus.SUBMITTED
    assert result.method == ApplicationMethod.EMAIL
    assert len(transport.messages) == 1

    message = transport.messages[0]

    assert message["From"] == "harshraj@example.com"
    assert message["To"] == "careers@example.com"
    assert message["Subject"] == (
        "Application for Hardware Design Engineer at Example Electronics"
    )
    assert "I am Harshraj." in message.get_body().get_content()

    attachments = list(message.iter_attachments())
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "resume.pdf"
    assert attachments[0].get_payload(decode=True) == b"fake pdf content"


def test_email_adapter_rejects_missing_recruiter_email(
    tmp_path: Path,
) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"fake pdf content")

    template = tmp_path / "template.txt"
    template.write_text(
        "Subject: Test\n\nBody",
        encoding="utf-8",
    )

    transport = FakeEmailTransport()
    adapter = EmailApplicationAdapter(
        candidate=make_candidate(resume),
        builder=EmailBuilder(template),
        transport=transport,
    )

    request = ApplicationRequest(
        source="adzuna",
        source_job_id="12345",
        job_title="Hardware Engineer",
        company="Example Electronics",
        application_method=ApplicationMethod.EMAIL,
    )

    result = adapter.submit(request)

    assert result.status == ApplicationStatus.FAILED
    assert result.message == "email application requires a recruiter email"
    assert transport.messages == []


def test_email_adapter_rejects_missing_resume(tmp_path: Path) -> None:
    template = tmp_path / "template.txt"
    template.write_text(
        "Subject: Test\n\nBody",
        encoding="utf-8",
    )

    candidate = CandidateProfile(
        full_name="Harshraj",
        email="harshraj@example.com",
        phone="9876543210",
    )

    transport = FakeEmailTransport()
    adapter = EmailApplicationAdapter(
        candidate=candidate,
        builder=EmailBuilder(template),
        transport=transport,
    )

    result = adapter.submit(make_request())

    assert result.status == ApplicationStatus.FAILED
    assert result.message == "email application requires a resume path"
    assert transport.messages == []


def test_email_adapter_rejects_nonexistent_resume(
    tmp_path: Path,
) -> None:
    template = tmp_path / "template.txt"
    template.write_text(
        "Subject: Test\n\nBody",
        encoding="utf-8",
    )

    candidate = make_candidate(tmp_path / "missing.pdf")

    transport = FakeEmailTransport()
    adapter = EmailApplicationAdapter(
        candidate=candidate,
        builder=EmailBuilder(template),
        transport=transport,
    )

    result = adapter.submit(make_request())

    assert result.status == ApplicationStatus.FAILED
    assert "resume file not found" in result.message
    assert transport.messages == []


def test_email_adapter_rejects_browser_request(
    tmp_path: Path,
) -> None:
    resume = tmp_path / "resume.pdf"
    resume.write_bytes(b"fake pdf content")

    template = tmp_path / "template.txt"
    template.write_text(
        "Subject: Test\n\nBody",
        encoding="utf-8",
    )

    transport = FakeEmailTransport()
    adapter = EmailApplicationAdapter(
        candidate=make_candidate(resume),
        builder=EmailBuilder(template),
        transport=transport,
    )

    request = ApplicationRequest(
        source="adzuna",
        source_job_id="12345",
        job_title="Hardware Engineer",
        company="Example Electronics",
        application_method=ApplicationMethod.BROWSER,
        apply_url="https://example.com/apply",
    )

    result = adapter.submit(request)

    assert result.status == ApplicationStatus.FAILED
    assert (
        result.message
        == "email adapter received a non-email application method"
    )
    assert transport.messages == []
