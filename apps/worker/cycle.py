from packages.application.application_service import ApplicationService
from packages.application.approval import ApplicationApprovalService
from packages.application.discovery.target_discovery import ApplyTargetDiscovery
from packages.application.execution_policy import (
    ApplicationExecutionAction,
    ApplicationExecutionPolicy,
)
from packages.application.models import (
    ApplicationApprovalRequest,
    ApplicationExecutionMode,
    ApplicationMethod,
    ApplicationRequest,
    ApplicationStatus,
)
from packages.application.recovery import ApplicationRecoveryService
from packages.application.recovery_executor import ApplicationRecoveryExecutor
from packages.application.stats import ApplicationRunStats
from packages.common.config import Settings
from packages.domain.job import Job
from packages.domain.lifecycle import JobLifecycle
from packages.ingestion.service import IngestionService
from packages.job_sources.adzuna.client import AdzunaClient
from packages.job_sources.adzuna.source import AdzunaJobSource
from packages.job_sources.base import JobSource
from packages.matching.decision import DecisionAction, JobDecisionEngine
from packages.matching.evaluation import JobEvaluationService
from packages.matching.ranking import JobRankingEngine
from packages.matching.relevance import JobRelevanceEngine
from packages.persistence.application_repository import ApplicationRepository
from packages.persistence.decision_repository import DecisionRepository
from packages.persistence.job_repository import JobRepository


def process_application(
    job: Job,
    decision_action: DecisionAction,
    job_repository: JobRepository,
    application_service: ApplicationService,
    application_repository: ApplicationRepository,
    target_discovery: ApplyTargetDiscovery,
    stats: ApplicationRunStats | None = None,
    approval_service: ApplicationApprovalService | None = None,
    execution_mode: ApplicationExecutionMode = ApplicationExecutionMode.DRY_RUN,
) -> str:
    """Prepare an application for an APPLY decision."""

    if decision_action != DecisionAction.APPLY:
        return "not_applicable"

    if stats is not None:
        stats.apply_decisions += 1

    if job.source_job_id is None:
        raise ValueError(
            f"Cannot prepare application for job without source_job_id: "
            f"{job.title!r}."
        )

    job_id = job_repository.get_id_by_source_job_id(
        source=job.source,
        source_job_id=job.source_job_id,
    )

    if job_id is None:
        raise ValueError(
            f"Cannot find database ID for job: {job.title!r}."
        )

    target = target_discovery.discover(job)

    if target.method.value == "none":
        if stats is not None:
            stats.record_no_target()

        print(
            f"Application: NO TARGET | "
            f"Job: {job.title!r} | "
            f"Reason: {target.reason}"
        )
        return "no_target"

    if target.method.value == "browser":
        application_method = ApplicationMethod.BROWSER
    elif target.method.value == "email":
        application_method = ApplicationMethod.EMAIL
    else:
        raise ValueError(
            f"Unsupported application target method: "
            f"{target.method.value!r}"
        )

    if stats is not None:
        stats.record_target_found()

    target_value = (
        target.apply_url
        if application_method == ApplicationMethod.BROWSER
        else target.recruiter_email
    )

    latest_application = application_repository.get_latest(job_id)
    active_statuses = {
        ApplicationStatus.PENDING,
        ApplicationStatus.IN_PROGRESS,
        ApplicationStatus.PAUSED,
    }

    execution_policy = ApplicationExecutionPolicy()
    policy_result = execution_policy.evaluate(
        decision_action=decision_action,
        application_method=application_method,
        target_value=target_value,
        already_submitted=application_repository.has_submitted_application(
            job_id
        ),
        active_attempt=(
            latest_application is not None
            and latest_application.status in active_statuses
        ),
        execution_mode=execution_mode,
    )

    if policy_result.action == ApplicationExecutionAction.BLOCK:
        if (
            execution_mode == ApplicationExecutionMode.APPROVAL_REQUIRED
            and policy_result.reason
            == "explicit application approval is required before submission"
            and approval_service is not None
        ):
            approval = approval_service.request(
                ApplicationApprovalRequest(
                    source=job.source,
                    source_job_id=job.source_job_id,
                    job_title=job.title,
                    company=job.company,
                    application_method=application_method,
                    apply_url=target.apply_url,
                    recruiter_email=target.recruiter_email,
                    reason=(
                        "application requires explicit approval before "
                        "submission"
                    ),
                ),
                job_id=job_id,
            )
            print(
                f"Application: APPROVAL PENDING | "
                f"Approval ID: {approval.id} | "
                f"Method: {application_method.value} | "
                f"Job: {job.title!r}"
            )
            return "approval_pending"

        print(
            f"Application: BLOCKED | "
            f"Method: {application_method.value} | "
            f"Job: {job.title!r} | "
            f"Reason: {policy_result.reason}"
        )
        return "blocked"

    request = ApplicationRequest(
        source=job.source,
        source_job_id=job.source_job_id,
        job_title=job.title,
        company=job.company,
        application_method=application_method,
        apply_url=target.apply_url,
        recruiter_email=target.recruiter_email,
        execution_mode=execution_mode,
        submission_authorized=(
            policy_result.action == ApplicationExecutionAction.ALLOW
        ),
    )

    result = application_service.submit(
        request=request,
        job_id=job_id,
    )

    if stats is not None:
        stats.record_result(result.status)

    print(
        f"Application: {result.status.value.upper()} | "
        f"Method: {result.method.value} | "
        f"Job: {job.title!r} | "
        f"Message: {result.message}"
    )

    return result.status.value


def process_source(
    source: JobSource,
    repository: JobRepository,
    decision_repository: DecisionRepository,
    application_service: ApplicationService | None = None,
    application_repository: ApplicationRepository | None = None,
    target_discovery: ApplyTargetDiscovery | None = None,
    stats: ApplicationRunStats | None = None,
    approval_service: ApplicationApprovalService | None = None,
    execution_mode: ApplicationExecutionMode = ApplicationExecutionMode.DRY_RUN,
) -> tuple[int, int, int]:
    """Ingest, evaluate, rank, decide, and optionally prepare applications."""

    ingestion = IngestionService(
        source=source,
        repository=repository,
    )

    evaluation = JobEvaluationService(
        relevance_engine=JobRelevanceEngine(),
        lifecycle=JobLifecycle(),
        repository=repository,
    )

    ranking = JobRankingEngine()
    decision = JobDecisionEngine()

    jobs = ingestion.ingest()

    evaluated_count = 0
    ignored_count = 0
    application_stats = stats or ApplicationRunStats()

    for job in jobs:
        relevance_result = evaluation.evaluate(job)
        ranking_result = ranking.rank(job)
        decision_result = decision.decide(
            job=job,
            relevance=relevance_result,
            ranking=ranking_result,
        )

        if job.source_job_id is None:
            raise ValueError(
                f"Cannot persist decision for job without source_job_id: "
                f"{job.title!r}."
            )

        decision_repository.save(
            source=job.source,
            source_job_id=job.source_job_id,
            action=decision_result.action,
            relevance_score=relevance_result.score,
            ranking_score=ranking_result.score,
            priority=ranking_result.priority,
            reasons=decision_result.reasons,
        )

        if relevance_result.is_relevant:
            evaluated_count += 1
        else:
            ignored_count += 1

        print(
            f"Job: {job.title!r} | "
            f"Score: {ranking_result.score:.1f} | "
            f"Priority: {ranking_result.priority} | "
            f"Decision: {decision_result.action.value}"
        )

        if (
            application_service is not None
            and application_repository is not None
            and target_discovery is not None
        ):
            process_application(
                job=job,
                decision_action=decision_result.action,
                job_repository=repository,
                application_service=application_service,
                application_repository=application_repository,
                target_discovery=target_discovery,
                stats=application_stats,
                approval_service=approval_service,
                execution_mode=execution_mode,
            )

    return len(jobs), evaluated_count, ignored_count


def run_recovery_phase(
    job_repository: JobRepository,
    application_repository: ApplicationRepository,
    target_discovery: ApplyTargetDiscovery,
    application_service: ApplicationService,
    stats: ApplicationRunStats,
    execution_mode: ApplicationExecutionMode,
) -> None:
    """Run safe recovery attempts for retryable applications."""

    if execution_mode != ApplicationExecutionMode.FULL_AUTO:
        print(
            "Recovery: skipped because execution mode is "
            f"{execution_mode.value}"
        )
        return

    recovery_service = ApplicationRecoveryService(
        repository=application_repository,
    )

    recovery_executor = ApplicationRecoveryExecutor(
        job_repository=job_repository,
        application_repository=application_repository,
        target_discovery=target_discovery,
        application_service=application_service,
    )

    candidates = recovery_service.build_retry_plan()
    stats.recovery_candidates = len(candidates)

    print("=" * 60)
    print("Application Recovery")
    print("=" * 60)

    if not candidates:
        print("No failed applications are eligible for retry.")
    else:
        print(f"Recovery candidates: {len(candidates)}")

        for candidate in candidates:
            print(
                f"Recovery: job_id={candidate.job_id} "
                f"application_id={candidate.application_id} "
                f"method={candidate.method}"
            )

            try:
                plan, result = recovery_executor.execute(candidate)

                if result is None:
                    stats.recovery_skipped += 1
                    print(f"Recovery skipped: {plan.message}")
                    continue

                stats.record_recovery_result(result.status)

                print(
                    f"Recovery result: {result.status.value} | "
                    f"{result.message}"
                )

            except Exception as exc:
                stats.recovery_failed += 1
                print(
                    f"Recovery execution error: "
                    f"job_id={candidate.job_id} | {exc}"
                )


class WorkerCycle:
    """Runs one complete discovery, application, and recovery cycle."""

    def __init__(
        self,
        settings: Settings,
        client: AdzunaClient,
        repository: JobRepository,
        decision_repository: DecisionRepository,
        application_repository: ApplicationRepository,
        application_service: ApplicationService,
        target_discovery: ApplyTargetDiscovery,
        approval_service: ApplicationApprovalService | None = None,
    ) -> None:
        self.settings = settings
        self.client = client
        self.repository = repository
        self.decision_repository = decision_repository
        self.application_repository = application_repository
        self.application_service = application_service
        self.target_discovery = target_discovery
        self.approval_service = approval_service

    def run_cycle(self) -> None:
        total_new_jobs = 0
        total_evaluated_jobs = 0
        total_ignored_jobs = 0
        total_application_stats = ApplicationRunStats()

        for query in self.settings.adzuna_queries:
            source = AdzunaJobSource(
                client=self.client,
                query=query,
                pages=self.settings.adzuna_pages,
            )

            print("=" * 60)
            print(f"Processing query: {query}")
            print("=" * 60)

            application_stats = ApplicationRunStats()

            new_count, evaluated_count, ignored_count = process_source(
                source=source,
                repository=self.repository,
                decision_repository=self.decision_repository,
                application_service=self.application_service,
                application_repository=self.application_repository,
                target_discovery=self.target_discovery,
                stats=application_stats,
                execution_mode=self.settings.application_execution_mode,
                approval_service=self.approval_service,
            )

            total_new_jobs += new_count
            total_evaluated_jobs += evaluated_count
            total_ignored_jobs += ignored_count

            total_application_stats.apply_decisions += (
                application_stats.apply_decisions
            )
            total_application_stats.targets_found += (
                application_stats.targets_found
            )
            total_application_stats.no_target += application_stats.no_target
            total_application_stats.submitted += application_stats.submitted
            total_application_stats.pending += application_stats.pending
            total_application_stats.failed += application_stats.failed
            total_application_stats.paused += application_stats.paused
            total_application_stats.already_submitted += (
                application_stats.already_submitted
            )

            print(
                f"Query: {query!r} | "
                f"New jobs: {new_count} | "
                f"Evaluated: {evaluated_count} | "
                f"Ignored: {ignored_count}"
            )

            print(
                f"Applications: APPLY={application_stats.apply_decisions} | "
                f"Targets={application_stats.targets_found} | "
                f"No target={application_stats.no_target} | "
                f"Submitted={application_stats.submitted} | "
                f"Pending={application_stats.pending} | "
                f"Failed={application_stats.failed} | "
                f"Paused={application_stats.paused} | "
                f"Already submitted="
                f"{application_stats.already_submitted}"
            )

        run_recovery_phase(
            job_repository=self.repository,
            application_repository=self.application_repository,
            target_discovery=self.target_discovery,
            application_service=self.application_service,
            stats=total_application_stats,
            execution_mode=self.settings.application_execution_mode,
        )

        print("=" * 60)
        print(f"Total new jobs: {total_new_jobs}")
        print(f"Total evaluated jobs: {total_evaluated_jobs}")
        print(f"Total ignored jobs: {total_ignored_jobs}")
        print("=" * 60)
        print("Application Run Summary")
        print("=" * 60)
        print(
            f"Apply decisions   : "
            f"{total_application_stats.apply_decisions}"
        )
        print(
            f"Targets found     : "
            f"{total_application_stats.targets_found}"
        )
        print(
            f"No target         : "
            f"{total_application_stats.no_target}"
        )
        print(
            f"Submitted         : "
            f"{total_application_stats.submitted}"
        )
        print(
            f"Pending           : "
            f"{total_application_stats.pending}"
        )
        print(
            f"Failed            : "
            f"{total_application_stats.failed}"
        )
        print(
            f"Paused            : "
            f"{total_application_stats.paused}"
        )
        print(
            "Already submitted: "
            f"{total_application_stats.already_submitted}"
        )
        print(
            f"Recovery candidates: "
            f"{total_application_stats.recovery_candidates}"
        )
        print(
            f"Recovery submitted: "
            f"{total_application_stats.recovery_submitted}"
        )
        print(
            f"Recovery failed: "
            f"{total_application_stats.recovery_failed}"
        )
        print(
            f"Recovery paused: "
            f"{total_application_stats.recovery_paused}"
        )
        print(
            f"Recovery skipped: "
            f"{total_application_stats.recovery_skipped}"
        )
