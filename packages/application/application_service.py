from packages.application.adapters.base import ApplicationAdapter
from packages.application.models import (
    ApplicationMethod,
    ApplicationRequest,
    ApplicationResult,
    ApplicationStatus,
)
from packages.persistence.application_repository import (
    ApplicationRecord,
    ApplicationRepository,
)


class ApplicationService:
    """Coordinate application submission and persistence."""

    def __init__(
        self,
        email_adapter: ApplicationAdapter,
        browser_adapter: ApplicationAdapter,
        repository: ApplicationRepository | None = None,
    ) -> None:
        self.email_adapter = email_adapter
        self.browser_adapter = browser_adapter
        self.repository = repository

    def submit(
        self,
        request: ApplicationRequest,
        job_id: int | None = None,
    ) -> ApplicationResult:
        """Submit through the selected adapter and persist the result."""

        if job_id is not None and self.repository is not None:
            if self.repository.has_submitted_application(job_id):
                return ApplicationResult(
                    status=ApplicationStatus.ALREADY_SUBMITTED,
                    method=request.application_method,
                    message="job already has a submitted application",
                )

        if request.application_method == ApplicationMethod.EMAIL:
            result = self.email_adapter.submit(request)
        elif request.application_method == ApplicationMethod.BROWSER:
            result = self.browser_adapter.submit(request)
        else:
            raise ValueError(
                f"Unsupported application method: "
                f"{request.application_method.value!r}"
            )

        if job_id is not None and self.repository is not None:
            self.repository.save(
                ApplicationRecord(
                    job_id=job_id,
                    method=result.method,
                    status=result.status,
                    apply_url=request.apply_url,
                    recruiter_email=request.recruiter_email,
                    external_reference=result.external_reference,
                    message=result.message,
                )
            )

        return result
