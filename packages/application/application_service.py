from datetime import datetime, timezone

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
    """Coordinate crash-safe application submission and persistence."""

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
        """Submit through the selected adapter using a persisted lifecycle."""

        if job_id is None or self.repository is None:
            return self._submit_without_persistence(request)

        if self.repository.has_submitted_application(job_id):
            return ApplicationResult(
                status=ApplicationStatus.ALREADY_SUBMITTED,
                method=request.application_method,
                message="job already has a submitted application",
            )

        latest = self.repository.get_latest(job_id)

        if latest is not None and latest.status in {
            ApplicationStatus.PENDING,
            ApplicationStatus.IN_PROGRESS,
            ApplicationStatus.PAUSED,
        }:
            return ApplicationResult(
                status=ApplicationStatus.PAUSED,
                method=latest.method,
                message=(
                    "job has an existing application attempt requiring "
                    "manual recovery before another submission"
                ),
                external_reference=latest.external_reference,
            )

        started_at = datetime.now(timezone.utc)

        application_id = self.repository.save(
            ApplicationRecord(
                job_id=job_id,
                method=request.application_method,
                status=ApplicationStatus.PENDING,
                apply_url=request.apply_url,
                recruiter_email=request.recruiter_email,
                message="application attempt created",
                started_at=started_at,
            )
        )

        self.repository.update(
            application_id,
            status=ApplicationStatus.IN_PROGRESS,
            message="application submission started",
        )

        try:
            result = self._submit_with_adapter(request)
        except Exception as exc:
            self.repository.update(
                application_id,
                status=ApplicationStatus.PAUSED,
                message=f"application submission interrupted: {exc}",
            )

            return ApplicationResult(
                status=ApplicationStatus.PAUSED,
                method=request.application_method,
                message=(
                    "application submission was interrupted; "
                    "manual recovery is required"
                ),
            )

        self.repository.update(
            application_id,
            status=result.status,
            message=result.message,
            external_reference=result.external_reference,
            submitted_at=(
                datetime.now(timezone.utc)
                if result.status == ApplicationStatus.SUBMITTED
                else None
            ),
        )

        return result

    def _submit_without_persistence(
        self,
        request: ApplicationRequest,
    ) -> ApplicationResult:
        """Submit when no application repository/job ID is available."""

        return self._submit_with_adapter(request)

    def _submit_with_adapter(
        self,
        request: ApplicationRequest,
    ) -> ApplicationResult:
        """Dispatch an application request to the selected adapter."""

        if request.application_method == ApplicationMethod.EMAIL:
            return self.email_adapter.submit(request)

        if request.application_method == ApplicationMethod.BROWSER:
            return self.browser_adapter.submit(request)

        raise ValueError(
            f"Unsupported application method: "
            f"{request.application_method.value!r}"
        )
