import re

from packages.application.discovery.target import (
    ApplicationTarget,
    ApplicationTargetMethod,
)
from packages.domain.job import Job


class ApplyTargetDiscovery:
    """Determine the most suitable application destination for a job."""

    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    APPLY_URL_HINTS = (
        "/apply",
        "/application",
        "/careers",
        "/career",
    )

    def discover(self, job: Job) -> ApplicationTarget:
        """Discover an application URL or recruiter email from a job."""

        url_target = self._discover_url(job)
        if url_target is not None:
            return url_target

        email_target = self._discover_email(job)
        if email_target is not None:
            return email_target

        return ApplicationTarget(
            method=ApplicationTargetMethod.NONE,
            reason="no supported application target was found",
        )

    def _discover_url(self, job: Job) -> ApplicationTarget | None:
        """Use the source URL only when it appears to be an application URL."""

        url = str(job.source_url).strip()

        if not url:
            return None

        normalized_url = url.lower()

        if any(hint in normalized_url for hint in self.APPLY_URL_HINTS):
            return ApplicationTarget(
                method=ApplicationTargetMethod.BROWSER,
                apply_url=url,
                reason="source URL appears to be an application or careers page",
            )

        return None

    def _discover_email(self, job: Job) -> ApplicationTarget | None:
        """Extract the first email address from the job description."""

        if not job.description:
            return None

        match = self.EMAIL_PATTERN.search(job.description)

        if match is None:
            return None

        return ApplicationTarget(
            method=ApplicationTargetMethod.EMAIL,
            recruiter_email=match.group(0),
            reason="recruiter email found in job description",
        )
