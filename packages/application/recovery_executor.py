from dataclasses import dataclass
from enum import Enum

from packages.application.discovery.target import ApplicationTargetMethod
from packages.application.discovery.target_discovery import ApplyTargetDiscovery
from packages.application.models import ApplicationMethod
from packages.application.recovery import ApplicationRetryCandidate
from packages.domain.job import Job
from packages.persistence.application_repository import ApplicationRepository
from packages.persistence.job_repository import JobRepository


class RecoveryExecutionAction(str, Enum):
    READY = "ready"
    SKIP = "skip"


@dataclass(frozen=True)
class RecoveryExecutionPlan:
    job_id: int
    action: RecoveryExecutionAction
    application_method: ApplicationMethod | None = None
    apply_url: str | None = None
    recruiter_email: str | None = None
    message: str = ""


class ApplicationRecoveryExecutor:
    """Validate retry candidates against the current job and target."""

    def __init__(
        self,
        job_repository: JobRepository,
        application_repository: ApplicationRepository,
        target_discovery: ApplyTargetDiscovery,
    ) -> None:
        self.job_repository = job_repository
        self.application_repository = application_repository
        self.target_discovery = target_discovery

    def prepare(
        self,
        candidate: ApplicationRetryCandidate,
    ) -> RecoveryExecutionPlan:
        job = self._get_job(candidate.job_id)

        if job is None:
            return RecoveryExecutionPlan(
                job_id=candidate.job_id,
                action=RecoveryExecutionAction.SKIP,
                message="job no longer exists",
            )

        if self.application_repository.has_submitted_application(
            candidate.job_id
        ):
            return RecoveryExecutionPlan(
                job_id=candidate.job_id,
                action=RecoveryExecutionAction.SKIP,
                message="job already has a submitted application",
            )

        latest = self.application_repository.get_latest(candidate.job_id)

        if latest is None or latest.id != candidate.application_id:
            return RecoveryExecutionPlan(
                job_id=candidate.job_id,
                action=RecoveryExecutionAction.SKIP,
                message="retry candidate is no longer the latest application attempt",
            )

        target = self.target_discovery.discover(job)

        if target.method == ApplicationTargetMethod.NONE:
            return RecoveryExecutionPlan(
                job_id=candidate.job_id,
                action=RecoveryExecutionAction.SKIP,
                message="no current application target is available",
            )

        if target.method == ApplicationTargetMethod.EMAIL:
            if not target.recruiter_email:
                return RecoveryExecutionPlan(
                    job_id=candidate.job_id,
                    action=RecoveryExecutionAction.SKIP,
                    message="current email application target is invalid",
                )

            return RecoveryExecutionPlan(
                job_id=candidate.job_id,
                action=RecoveryExecutionAction.READY,
                application_method=ApplicationMethod.EMAIL,
                recruiter_email=target.recruiter_email,
                message="current email application target is valid",
            )

        if target.method == ApplicationTargetMethod.BROWSER:
            if not target.apply_url:
                return RecoveryExecutionPlan(
                    job_id=candidate.job_id,
                    action=RecoveryExecutionAction.SKIP,
                    message="current browser application target is invalid",
                )

            return RecoveryExecutionPlan(
                job_id=candidate.job_id,
                action=RecoveryExecutionAction.READY,
                application_method=ApplicationMethod.BROWSER,
                apply_url=target.apply_url,
                message="current browser application target is valid",
            )

        return RecoveryExecutionPlan(
            job_id=candidate.job_id,
            action=RecoveryExecutionAction.SKIP,
            message="unsupported application target",
        )

    def _get_job(self, job_id: int) -> Job | None:
        for job in self.job_repository.list_jobs():
            current_id = self.job_repository.get_id_by_source_job_id(
                job.source,
                job.source_job_id or "",
            )

            if current_id == job_id:
                return job

        return None
