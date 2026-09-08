from packages.application.adapters.base import ApplicationAdapter
from packages.application.models import (
    ApplicationRequest,
    ApplicationResult,
    ApplicationStatus,
)


class DryRunApplicationAdapter(ApplicationAdapter):
    """Validate an application request without submitting it."""

    def submit(self, request: ApplicationRequest) -> ApplicationResult:
        if request.application_method.value == "browser":
            if not request.apply_url:
                return ApplicationResult(
                    status=ApplicationStatus.FAILED,
                    method=request.application_method,
                    message="browser application requires an apply URL",
                )

        if request.application_method.value == "email":
            if not request.recruiter_email:
                return ApplicationResult(
                    status=ApplicationStatus.FAILED,
                    method=request.application_method,
                    message="email application requires a recruiter email",
                )

        return ApplicationResult(
            status=ApplicationStatus.PENDING,
            method=request.application_method,
            message="application request validated; no submission performed",
        )
