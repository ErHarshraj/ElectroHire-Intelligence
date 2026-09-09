from dataclasses import dataclass
from pathlib import Path

from packages.application.models import ApplicationRequest
from packages.application.profile import CandidateProfile


@dataclass(frozen=True)
class BuiltEmail:
    """Fully rendered application email."""

    subject: str
    body: str


class EmailBuilder:
    """Build a job-application email from a template."""

    def __init__(self, template_path: Path) -> None:
        self.template_path = template_path

    def build(
        self,
        request: ApplicationRequest,
        candidate: CandidateProfile,
    ) -> BuiltEmail:
        """Render an application email for a specific job."""

        template = self.template_path.read_text(encoding="utf-8")

        replacements = {
            "{{name}}": candidate.full_name,
            "{{company}}": request.company,
            "{{job_title}}": request.job_title,
            "{{candidate_email}}": candidate.email,
            "{{phone}}": candidate.phone,
            "{{location}}": candidate.location or "",
            "{{linkedin_url}}": candidate.linkedin_url or "",
            "{{github_url}}": candidate.github_url or "",
            "{{portfolio_url}}": candidate.portfolio_url or "",
        }

        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)

        lines = template.splitlines()

        if lines and lines[0].startswith("Subject:"):
            subject = lines[0].removeprefix("Subject:").strip()
            body = "\n".join(lines[1:]).strip()
        else:
            subject = "Application for Hardware Engineering Opportunities"
            body = template.strip()

        if not subject:
            raise ValueError("email template produced an empty subject")

        if not body:
            raise ValueError("email template produced an empty body")

        return BuiltEmail(
            subject=subject,
            body=body,
        )
