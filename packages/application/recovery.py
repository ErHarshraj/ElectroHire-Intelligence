from dataclasses import dataclass
from enum import Enum

from packages.application.models import ApplicationStatus
from packages.persistence.application_repository import (
    ApplicationRecord,
    ApplicationRepository,
)


class RecoveryAction(str, Enum):
    NONE = "none"
    INSPECT = "inspect"
    MANUAL_RECOVERY = "manual_recovery"
    RETRY = "retry"
    DO_NOT_RESUBMIT = "do_not_resubmit"


@dataclass(frozen=True)
class ApplicationRecoveryReport:
    job_id: int
    status: ApplicationStatus | None
    action: RecoveryAction
    message: str
    application_id: int | None = None


@dataclass(frozen=True)
class ApplicationRetryCandidate:
    job_id: int
    application_id: int
    method: str
    message: str


class ApplicationRecoveryService:
    """Classify application state and build a safe retry plan."""

    ACTIVE_STATUSES = {
        ApplicationStatus.PENDING,
        ApplicationStatus.IN_PROGRESS,
        ApplicationStatus.PAUSED,
    }

    def __init__(self, repository: ApplicationRepository) -> None:
        self.repository = repository

    def inspect(self, job_id: int) -> ApplicationRecoveryReport:
        """Inspect the latest application attempt without changing state."""

        latest = self.repository.get_latest(job_id)

        if latest is None:
            return ApplicationRecoveryReport(
                job_id=job_id,
                status=None,
                action=RecoveryAction.NONE,
                message="no previous application attempt exists",
            )

        return self._classify(latest)

    def build_retry_plan(self) -> list[ApplicationRetryCandidate]:
        """Return failed attempts that are currently safe to retry."""

        candidates: list[ApplicationRetryCandidate] = []

        for application in self.repository.list_retryable_attempts():
            if self.repository.has_submitted_application(application.job_id):
                continue

            latest = self.repository.get_latest(application.job_id)

            if latest is None:
                continue

            if latest.id != application.id:
                if latest.status in self.ACTIVE_STATUSES:
                    continue

                if latest.status in {
                    ApplicationStatus.SUBMITTED,
                    ApplicationStatus.ALREADY_SUBMITTED,
                }:
                    continue

            candidates.append(
                ApplicationRetryCandidate(
                    job_id=application.job_id,
                    application_id=application.id or 0,
                    method=application.method.value,
                    message="failed application attempt is eligible for retry",
                )
            )

        return candidates

    def _classify(
        self,
        application: ApplicationRecord,
    ) -> ApplicationRecoveryReport:
        if application.status == ApplicationStatus.PENDING:
            return ApplicationRecoveryReport(
                job_id=application.job_id,
                status=application.status,
                action=RecoveryAction.INSPECT,
                message=(
                    "application attempt exists in pending state; "
                    "inspect before retrying"
                ),
                application_id=application.id,
            )

        if application.status == ApplicationStatus.IN_PROGRESS:
            return ApplicationRecoveryReport(
                job_id=application.job_id,
                status=application.status,
                action=RecoveryAction.INSPECT,
                message=(
                    "application may have been interrupted while in progress; "
                    "automatic retry is not permitted"
                ),
                application_id=application.id,
            )

        if application.status == ApplicationStatus.PAUSED:
            return ApplicationRecoveryReport(
                job_id=application.job_id,
                status=application.status,
                action=RecoveryAction.MANUAL_RECOVERY,
                message="manual recovery is required before another submission",
                application_id=application.id,
            )

        if application.status == ApplicationStatus.FAILED:
            return ApplicationRecoveryReport(
                job_id=application.job_id,
                status=application.status,
                action=RecoveryAction.RETRY,
                message="failed application attempt is eligible for retry",
                application_id=application.id,
            )

        if application.status in {
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.ALREADY_SUBMITTED,
        }:
            return ApplicationRecoveryReport(
                job_id=application.job_id,
                status=application.status,
                action=RecoveryAction.DO_NOT_RESUBMIT,
                message="application was already submitted; do not resubmit",
                application_id=application.id,
            )

        return ApplicationRecoveryReport(
            job_id=application.job_id,
            status=application.status,
            action=RecoveryAction.INSPECT,
            message="application state requires inspection",
            application_id=application.id,
        )
