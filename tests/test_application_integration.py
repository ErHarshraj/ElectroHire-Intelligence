from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from packages.application.adapters.email import EmailApplicationAdapter
from packages.application.application_service import ApplicationService
from packages.application.discovery.target_discovery import ApplyTargetDiscovery
from packages.application.email.builder import EmailBuilder
from packages.application.email.transport import EmailTransport
from packages.application.models import (
    ApplicationMethod,
    ApplicationRequest,
    ApplicationStatus,
)
from packages.application.profile import CandidateProfile
from packages.domain.job import Job


class FakeEmailTransport(EmailTransport):
    def __init__(self) -> None:
        self.messages: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> None:
        self.messages.append(message)


class FakeApplicationRepository:
    def __init__(self) -> None:
        self.records = {}
        self.next_id = 1

    def save(self, record):
        application_id = self.next_id
        self.next_id += 1
        self.records[application_id] = record
        return application_id

    def get_latest(self, job_id):
        matching = [
            (application_id, record)
            for application_id, record in self.records.items()
            if record.job_id == job_id
        ]
        if not matching:
            return None

        _, record = max(matching, key=lambda item: item[0])

        return record

    def update(
        self,
        application_id,
        *,
        status,
        message="",
        external_reference=None,
        submitted_at=None,
    ):
        record = self.records[application_id]

        self.records[application_id] = type(record)(
            job_id=record.job_id,
            method=record.method,
            status=status,
            id=record.id,
            apply_url=record.apply_url,
            recruiter_email=record.recruiter_email,
            external_reference=external_reference,
            message=message,
            started_at=record.started_at,
            submitted_at=submitted_at,
        )

    def has_submitted_application(self, job_id):
        return any(
            record.job_id == job_id
            and record.status == ApplicationStatus.SUBMITTED
            for record in self.records.values()
        )


def test_email_application_end_to_end(tmp_path: Path) -> None:
    resume_path = tmp_path / "resume.pdf"
    resume_path.write_bytes(b"%PDF-test-resume")

    template_path = tmp_path / "job_application.txt"
    template_path.write_text(
        """Subject: Application for {{job_title}} at {{company}}

Dear Hiring Manager,

I am {{name}}.

Please consider my application for the {{job_title}} position at {{company}}.

Best regards,
{{name}}
{{candidate_email}}
{{phone}}
""",
        encoding="utf-8",
    )

    job = Job(
        title="Hardware Design Engineer",
        company="Example Electronics",
        location="India",
        description=(
            "Please send applications to careers@example.com"
        ),
        source="test",
        source_job_id="test-001",
        source_url="https://example.com/jobs/test-001",
        discovered_at=datetime.now(timezone.utc),
    )

    target = ApplyTargetDiscovery().discover(job)

    assert target.method.value == "email"
    assert target.recruiter_email == "careers@example.com"

    candidate = CandidateProfile(
        full_name="Harshraj",
        email="harshraj@example.com",
        phone="9876543210",
        location="India",
        resume_path=str(resume_path),
    )

    transport = FakeEmailTransport()

    adapter = EmailApplicationAdapter(
        candidate=candidate,
        builder=EmailBuilder(template_path),
        transport=transport,
    )

    repository = FakeApplicationRepository()

    service = ApplicationService(
        email_adapter=adapter,
        browser_adapter=adapter,
        repository=repository,
    )

    request = ApplicationRequest(
        source=job.source,
        source_job_id=job.source_job_id,
        job_title=job.title,
        company=job.company,
        application_method=ApplicationMethod.EMAIL,
        recruiter_email=target.recruiter_email,
    )

    result = service.submit(
        request=request,
        job_id=42,
    )

    assert result.status == ApplicationStatus.SUBMITTED
    assert result.method == ApplicationMethod.EMAIL
    assert result.message == "application email submitted successfully"

    assert len(transport.messages) == 1

    message = transport.messages[0]

    assert message["From"] == "harshraj@example.com"
    assert message["To"] == "careers@example.com"
    assert message["Subject"] == (
        "Application for Hardware Design Engineer at Example Electronics"
    )

    body = message.get_body(preferencelist=("plain",)).get_content()

    assert "Harshraj" in body
    assert "Hardware Design Engineer" in body
    assert "Example Electronics" in body

    attachments = list(message.iter_attachments())

    assert len(attachments) == 1
    assert attachments[0].get_filename() == "resume.pdf"
    assert attachments[0].get_content_type() == "application/pdf"
    assert attachments[0].get_payload(decode=True) == b"%PDF-test-resume"

    latest = repository.get_latest(42)

    assert latest is not None
    assert latest.status == ApplicationStatus.SUBMITTED
    assert latest.method == ApplicationMethod.EMAIL
