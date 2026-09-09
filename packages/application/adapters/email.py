from email.message import EmailMessage
from pathlib import Path

from packages.application.adapters.base import ApplicationAdapter
from packages.application.email.builder import EmailBuilder
from packages.application.email.transport import EmailTransport
from packages.application.models import (
    ApplicationRequest,
    ApplicationResult,
    ApplicationStatus,
)
from packages.application.profile import CandidateProfile


class EmailApplicationAdapter(ApplicationAdapter):
    """Submit an application through email."""

    def __init__(
        self,
        candidate: CandidateProfile,
        builder: EmailBuilder,
        transport: EmailTransport,
    ) -> None:
        self.candidate = candidate
        self.builder = builder
        self.transport = transport

    def submit(self, request: ApplicationRequest) -> ApplicationResult:
        if request.application_method.value != "email":
            return ApplicationResult(
                status=ApplicationStatus.FAILED,
                method=request.application_method,
                message="email adapter received a non-email application method",
            )

        if not request.recruiter_email:
            return ApplicationResult(
                status=ApplicationStatus.FAILED,
                method=request.application_method,
                message="email application requires a recruiter email",
            )

        if not self.candidate.resume_path:
            return ApplicationResult(
                status=ApplicationStatus.FAILED,
                method=request.application_method,
                message="email application requires a resume path",
            )

        resume_path = Path(self.candidate.resume_path)

        if not resume_path.is_file():
            return ApplicationResult(
                status=ApplicationStatus.FAILED,
                method=request.application_method,
                message=f"resume file not found: {resume_path}",
            )

        built_email = self.builder.build(request, self.candidate)

        message = EmailMessage()
        message["From"] = self.candidate.email
        message["To"] = request.recruiter_email
        message["Subject"] = built_email.subject
        message.set_content(built_email.body)

        message.add_attachment(
            resume_path.read_bytes(),
            maintype="application",
            subtype="pdf",
            filename=resume_path.name,
        )

        self.transport.send(message)

        return ApplicationResult(
            status=ApplicationStatus.SUBMITTED,
            method=request.application_method,
            message="application email submitted successfully",
        )
