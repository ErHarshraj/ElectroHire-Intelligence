from dataclasses import dataclass

from packages.application.models import ApplicationStatus


@dataclass
class ApplicationRunStats:
    """Track application execution results for one worker run."""

    apply_decisions: int = 0
    targets_found: int = 0
    no_target: int = 0
    submitted: int = 0
    pending: int = 0
    failed: int = 0
    paused: int = 0
    already_submitted: int = 0

    def record_target_found(self) -> None:
        self.targets_found += 1

    def record_no_target(self) -> None:
        self.no_target += 1

    def record_result(self, status: ApplicationStatus) -> None:
        if status == ApplicationStatus.SUBMITTED:
            self.submitted += 1
        elif status == ApplicationStatus.PENDING:
            self.pending += 1
        elif status == ApplicationStatus.FAILED:
            self.failed += 1
        elif status == ApplicationStatus.PAUSED:
            self.paused += 1
        elif status == ApplicationStatus.ALREADY_SUBMITTED:
            self.already_submitted += 1
