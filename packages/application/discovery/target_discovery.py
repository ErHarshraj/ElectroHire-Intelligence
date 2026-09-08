import re
from urllib.parse import urlparse

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

    APPLICATION_PATH_SEGMENTS = {
        "apply",
        "application",
        "career",
        "careers",
    }

    PREFERRED_EMAIL_LOCAL_PARTS = {
        "careers",
        "career",
        "jobs",
        "recruiting",
        "recruiter",
        "hiring",
        "hr",
    }

    GENERIC_EMAIL_LOCAL_PARTS = {
        "support",
        "sales",
        "info",
        "contact",
        "privacy",
        "legal",
    }

    def discover(self, job: Job) -> ApplicationTarget:
        """Discover the best available application destination."""

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
        """Use the source URL when its path contains an application segment."""

        url = str(job.source_url).strip()

        if not url:
            return None

        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None

        path_segments = {
            segment.lower()
            for segment in parsed.path.split("/")
            if segment
        }

        if not path_segments.intersection(self.APPLICATION_PATH_SEGMENTS):
            return None

        return ApplicationTarget(
            method=ApplicationTargetMethod.BROWSER,
            apply_url=url,
            reason="application URL detected from source URL path",
        )

    def _discover_email(self, job: Job) -> ApplicationTarget | None:
        """Extract and rank email candidates from the job description."""

        if not job.description:
            return None

        matches = self.EMAIL_PATTERN.findall(job.description)

        if not matches:
            return None

        emails = list(dict.fromkeys(email.lower() for email in matches))

        for email in emails:
            local_part = email.split("@", 1)[0]

            if local_part in self.PREFERRED_EMAIL_LOCAL_PARTS:
                return ApplicationTarget(
                    method=ApplicationTargetMethod.EMAIL,
                    recruiter_email=email,
                    reason="recruiting email found in job description",
                )

        for email in emails:
            local_part = email.split("@", 1)[0]

            if local_part not in self.GENERIC_EMAIL_LOCAL_PARTS:
                return ApplicationTarget(
                    method=ApplicationTargetMethod.EMAIL,
                    recruiter_email=email,
                    reason="non-generic contact email found in job description",
                )

        return ApplicationTarget(
            method=ApplicationTargetMethod.EMAIL,
            recruiter_email=emails[0],
            reason="generic contact email used as fallback from job description",
        )
