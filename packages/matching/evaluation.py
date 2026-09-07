from packages.domain.job import Job
from packages.domain.job_status import JobStatus
from packages.domain.lifecycle import JobLifecycle
from packages.matching.relevance import JobRelevanceEngine, RelevanceResult
from packages.persistence.job_repository import JobRepository


class JobEvaluationService:
    """Evaluate discovered jobs and persist their processing state."""

    def __init__(
        self,
        relevance_engine: JobRelevanceEngine,
        lifecycle: JobLifecycle,
        repository: JobRepository,
    ) -> None:
        self.relevance_engine = relevance_engine
        self.lifecycle = lifecycle
        self.repository = repository

    def evaluate(self, job: Job) -> RelevanceResult:
        """Evaluate one discovered job and persist its resulting state."""

        if job.status != JobStatus.DISCOVERED:
            raise ValueError(
                f"Only discovered jobs can be evaluated. "
                f"Current status: {job.status.value}."
            )

        result = self.relevance_engine.evaluate(job)

        new_status = (
            JobStatus.EVALUATED
            if result.is_relevant
            else JobStatus.IGNORED
        )

        self.lifecycle.transition(job, new_status)
        self.repository.save(job)

        return result
