from packages.domain.job import Job
from packages.domain.job_status import JobStatus


class InvalidJobStatusTransition(ValueError):
    """Raised when a job lifecycle transition is not allowed."""


class JobLifecycle:
    """Controls valid processing-state transitions for jobs."""

    _ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
        JobStatus.DISCOVERED: {JobStatus.EVALUATED, JobStatus.IGNORED},
        JobStatus.EVALUATED: {JobStatus.SHORTLISTED, JobStatus.IGNORED},
        JobStatus.SHORTLISTED: {JobStatus.IGNORED},
        JobStatus.IGNORED: set(),
    }

    def transition(self, job: Job, new_status: JobStatus) -> Job:
        """Move a job to a valid next lifecycle state."""

        allowed_statuses = self._ALLOWED_TRANSITIONS[job.status]

        if new_status not in allowed_statuses:
            raise InvalidJobStatusTransition(
                f"Cannot transition job from {job.status.value} "
                f"to {new_status.value}."
            )

        job.status = new_status
        return job
