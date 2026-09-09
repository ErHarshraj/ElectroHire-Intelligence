from pathlib import Path

from packages.application.adapters.dry_run import DryRunApplicationAdapter
from packages.application.adapters.email import EmailApplicationAdapter
from packages.application.application_service import ApplicationService
from packages.application.discovery.target_discovery import ApplyTargetDiscovery
from packages.application.email.builder import EmailBuilder
from packages.application.email.smtp import SMTPEmailTransport
from packages.application.models import ApplicationMethod, ApplicationRequest
from packages.application.profile import CandidateProfile
from packages.application.stats import ApplicationRunStats
from packages.common.config import Settings, get_settings
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
from packages.persistence.database import SessionLocal, create_tables
from packages.persistence.decision_repository import DecisionRepository
from packages.persistence.job_repository import JobRepository
from packages.persistence.sqlalchemy_application_repository import (
    SQLAlchemyApplicationRepository,
)
from packages.persistence.sqlalchemy_decision_repository import (
    SQLAlchemyDecisionRepository,
)
from packages.persistence.sqlalchemy_job_repository import SQLAlchemyJobRepository


def process_application(
    job: Job,
    decision_action: DecisionAction,
    job_repository: JobRepository,
    application_service: ApplicationService,
    target_discovery: ApplyTargetDiscovery,
    stats: ApplicationRunStats | None = None,
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
            f"Unsupported application target method: {target.method.value!r}"
        )

    if stats is not None:
        stats.record_target_found()

    request = ApplicationRequest(
        source=job.source,
        source_job_id=job.source_job_id,
        job_title=job.title,
        company=job.company,
        application_method=application_method,
        apply_url=target.apply_url,
        recruiter_email=target.recruiter_email,
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
    application_repository: ApplicationRepository | None = None,
    application_service: ApplicationService | None = None,
    target_discovery: ApplyTargetDiscovery | None = None,
    stats: ApplicationRunStats | None = None,
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
            and target_discovery is not None
        ):
            process_application(
                job=job,
                decision_action=decision_result.action,
                job_repository=repository,
                application_service=application_service,
                target_discovery=target_discovery,
                stats=application_stats,
            )

    return len(jobs), evaluated_count, ignored_count


def build_application_service(
    settings: Settings,
    application_repository: ApplicationRepository,
) -> ApplicationService:
    """Build the application service from runtime configuration."""

    dry_run_adapter = DryRunApplicationAdapter()

    if not settings.email_enabled:
        return ApplicationService(
            email_adapter=dry_run_adapter,
            browser_adapter=dry_run_adapter,
            repository=application_repository,
        )

    required_email_settings = {
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "smtp_username": settings.smtp_username,
        "smtp_password": settings.smtp_password,
        "candidate_email": settings.candidate_email,
        "candidate_phone": settings.candidate_phone,
        "candidate_resume_path": settings.candidate_resume_path,
    }

    missing_settings = [
        name
        for name, value in required_email_settings.items()
        if value is None
        or (isinstance(value, str) and not value.strip())
    ]

    if missing_settings:
        raise RuntimeError(
            "Email sending is enabled but required settings are missing: "
            + ", ".join(missing_settings)
        )

    smtp_host = settings.smtp_host
    smtp_port = settings.smtp_port
    smtp_username = settings.smtp_username
    smtp_password = settings.smtp_password
    candidate_email = settings.candidate_email
    candidate_phone = settings.candidate_phone
    candidate_resume_path = settings.candidate_resume_path

    assert smtp_host is not None
    assert smtp_port is not None
    assert smtp_username is not None
    assert smtp_password is not None
    assert candidate_email is not None
    assert candidate_phone is not None
    assert candidate_resume_path is not None

    candidate = CandidateProfile(
        full_name=settings.candidate_name,
        email=candidate_email,
        phone=candidate_phone,
        location=settings.candidate_location,
        resume_path=candidate_resume_path,
        linkedin_url=settings.candidate_linkedin_url,
        github_url=settings.candidate_github_url,
        portfolio_url=settings.candidate_portfolio_url,
    )

    template_path = Path("templates/job_application.txt")

    if not template_path.is_file():
        raise RuntimeError(
            f"Email template not found: {template_path.resolve()}"
        )

    resume_path = Path(candidate_resume_path)

    if not resume_path.is_file():
        raise RuntimeError(
            f"Candidate resume not found: {resume_path.resolve()}"
        )

    email_builder = EmailBuilder(
        template_path=template_path,
    )

    smtp_transport = SMTPEmailTransport(
        host=smtp_host,
        port=smtp_port,
        username=smtp_username,
        password=smtp_password,
    )

    email_adapter = EmailApplicationAdapter(
        candidate=candidate,
        builder=email_builder,
        transport=smtp_transport,
    )

    return ApplicationService(
        email_adapter=email_adapter,
        browser_adapter=dry_run_adapter,
        repository=application_repository,
    )


def run() -> None:
    settings = get_settings()

    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        raise RuntimeError(
            "Adzuna credentials are not configured. "
            "Set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env."
        )

    create_tables()

    session = SessionLocal()

    try:
        client = AdzunaClient(
            app_id=settings.adzuna_app_id,
            app_key=settings.adzuna_app_key,
            country=settings.adzuna_country,
        )

        repository = SQLAlchemyJobRepository(session)
        decision_repository = SQLAlchemyDecisionRepository(session)
        application_repository = SQLAlchemyApplicationRepository(session)

        application_service = build_application_service(
            settings=settings,
            application_repository=application_repository,
        )

        target_discovery = ApplyTargetDiscovery()

        total_new_jobs = 0
        total_evaluated_jobs = 0
        total_ignored_jobs = 0
        total_application_stats = ApplicationRunStats()

        for query in settings.adzuna_queries:
            source = AdzunaJobSource(
                client=client,
                query=query,
                pages=settings.adzuna_pages,
            )

            print("=" * 60)
            print(f"Processing query: {query}")
            print("=" * 60)

            application_stats = ApplicationRunStats()

            new_count, evaluated_count, ignored_count = process_source(
                source=source,
                repository=repository,
                decision_repository=decision_repository,
                application_repository=application_repository,
                application_service=application_service,
                target_discovery=target_discovery,
                stats=application_stats,
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
                f"Already submitted={application_stats.already_submitted}"
            )

        print(f"Total new jobs: {total_new_jobs}")
        print(f"Total evaluated jobs: {total_evaluated_jobs}")
        print(f"Total ignored jobs: {total_ignored_jobs}")
        print("=" * 60)
        print("Application Run Summary")
        print("=" * 60)
        print(f"Apply decisions   : {total_application_stats.apply_decisions}")
        print(f"Targets found     : {total_application_stats.targets_found}")
        print(f"No target         : {total_application_stats.no_target}")
        print(f"Submitted         : {total_application_stats.submitted}")
        print(f"Pending           : {total_application_stats.pending}")
        print(f"Failed            : {total_application_stats.failed}")
        print(f"Paused            : {total_application_stats.paused}")
        print(
            "Already submitted: "
            f"{total_application_stats.already_submitted}"
        )

    finally:
        session.close()


if __name__ == "__main__":
    run()
