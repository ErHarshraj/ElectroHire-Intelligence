from datetime import datetime, timezone

from packages.application.application_service import ApplicationService
from packages.application.approval import ApplicationApprovalService
from packages.application.discovery.target import ApplicationTargetMethod
from packages.application.discovery.target_discovery import ApplyTargetDiscovery
from packages.application.models import (
    ApplicationExecutionMode,
    ApplicationMethod,
    ApplicationRequest,
    ApplicationStatus,
)
from packages.matching.decision import DecisionAction
from packages.persistence.application_approval_repository import (
    ApplicationApprovalRecord,
)
from packages.persistence.application_repository import ApplicationRepository
from packages.persistence.decision_repository import DecisionRepository
from packages.persistence.job_repository import JobRepository


class ApplicationApprovalExecutor:
    """Execute approved applications after revalidating current job state."""

    def __init__(
        self,
        approval_service: ApplicationApprovalService,
        job_repository: JobRepository,
        decision_repository: DecisionRepository,
        application_repository: ApplicationRepository,
        application_service: ApplicationService,
        target_discovery: ApplyTargetDiscovery,
    ) -> None:
        self.approval_service = approval_service
        self.job_repository = job_repository
        self.decision_repository = decision_repository
        self.application_repository = application_repository
        self.application_service = application_service
        self.target_discovery = target_discovery

    def execute(
        self,
        approval: ApplicationApprovalRecord,
    ) -> ApplicationStatus:
        """Execute one approved application after validating current state."""

        if approval.id is None:
            raise ValueError("cannot execute approval without an ID")

        if approval.status.value != "approved":
            raise ValueError(
                f"application approval {approval.id} is not approved"
            )

        if approval.consumed_at is not None:
            raise ValueError(
                f"application approval {approval.id} has already been consumed"
            )

        job = self.job_repository.get_by_source_job_id(
            source=approval.source,
            source_job_id=approval.source_job_id,
        )

        if job is None:
            raise ValueError(
                f"approved job no longer exists: "
                f"{approval.source!r}/{approval.source_job_id!r}"
            )

        if not job.is_active:
            raise ValueError(
                f"approved job is no longer active: {job.title!r}"
            )

        decisions = self.decision_repository.list_for_job(
            source=approval.source,
            source_job_id=approval.source_job_id,
        )

        if not decisions:
            raise ValueError(
                f"approved job has no persisted decision: {job.title!r}"
            )

        latest_decision = decisions[-1]

        if latest_decision.action != DecisionAction.APPLY:
            raise ValueError(
                "latest job decision no longer permits application: "
                f"{latest_decision.action.value}"
            )

        target = self.target_discovery.discover(job)

        if target.method == ApplicationTargetMethod.BROWSER:
            current_method = ApplicationMethod.BROWSER
            current_target = target.apply_url
            approved_target = approval.apply_url

        elif target.method == ApplicationTargetMethod.EMAIL:
            current_method = ApplicationMethod.EMAIL
            current_target = target.recruiter_email
            approved_target = approval.recruiter_email

        else:
            raise ValueError(
                "application target is no longer available"
            )

        if current_method != approval.method:
            raise ValueError(
                "application target method changed since approval"
            )

        if not current_target:
            raise ValueError(
                "application target is no longer available"
            )

        if current_target != approved_target:
            raise ValueError(
                "application target changed since approval"
            )

        job_id = self.job_repository.get_id_by_source_job_id(
            source=approval.source,
            source_job_id=approval.source_job_id,
        )

        if job_id is None:
            raise ValueError(
                f"cannot find database ID for approved job: {job.title!r}"
            )

        request = ApplicationRequest(
            source=job.source,
            source_job_id=approval.source_job_id,
            job_title=job.title,
            company=job.company,
            application_method=approval.method,
            apply_url=target.apply_url,
            recruiter_email=target.recruiter_email,
            execution_mode=ApplicationExecutionMode.FULL_AUTO,
            submission_authorized=True,
        )

        result = self.application_service.submit(
            request=request,
            job_id=job_id,
        )

        if result.status in {
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.ALREADY_SUBMITTED,
        }:
            self.approval_service.consume(
                approval.id,
                datetime.now(timezone.utc),
            )

        return result.status
