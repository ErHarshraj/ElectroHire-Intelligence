from pathlib import Path

from sqlalchemy.orm import Session

from apps.worker.cycle import WorkerCycle, process_source
from packages.application.adapters.browser import BrowserApplicationAdapter
from packages.application.adapters.dry_run import DryRunApplicationAdapter
from packages.application.adapters.email import EmailApplicationAdapter
from packages.application.application_service import ApplicationService
from packages.application.discovery.target_discovery import ApplyTargetDiscovery
from packages.application.email.builder import EmailBuilder
from packages.application.email.smtp import SMTPEmailTransport
from packages.application.profile import CandidateProfile
from packages.application.recovery import ApplicationRecoveryService
from packages.application.recovery_executor import ApplicationRecoveryExecutor
from packages.application.stats import ApplicationRunStats
from packages.common.config import Settings, get_settings
from packages.job_sources.adzuna.client import AdzunaClient
from packages.persistence.application_repository import ApplicationRepository
from packages.persistence.database import SessionLocal, create_tables
from packages.persistence.job_repository import JobRepository
from packages.persistence.sqlalchemy_application_repository import (
    SQLAlchemyApplicationRepository,
)
from packages.persistence.sqlalchemy_decision_repository import (
    SQLAlchemyDecisionRepository,
)
from packages.persistence.sqlalchemy_job_repository import (
    SQLAlchemyJobRepository,
)
from packages.scheduler.models import SchedulerConfig
from packages.scheduler.service import ScheduledWork, SchedulerService

__all__ = [
    "WorkerCycle",
    "process_source",
    "run_recovery_phase",
    "build_application_service",
    "build_worker_cycle",
    "run",
    "run_scheduled",
]


def run_recovery_phase(
    job_repository: JobRepository,
    application_repository: ApplicationRepository,
    target_discovery: ApplyTargetDiscovery,
    application_service: ApplicationService,
    stats: ApplicationRunStats,
) -> None:
    """Compatibility wrapper for the legacy worker recovery API."""

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

    for candidate in candidates:
        try:
            _, result = recovery_executor.execute(candidate)

            if result is None:
                stats.recovery_skipped += 1
                continue

            stats.record_recovery_result(result.status)

        except Exception:
            stats.recovery_failed += 1


def build_application_service(
    settings: Settings,
    application_repository: SQLAlchemyApplicationRepository,
) -> ApplicationService:
    """Build the application service from runtime configuration."""

    dry_run_adapter = DryRunApplicationAdapter()

    if settings.browser_enabled:
        if not settings.candidate_email:
            raise RuntimeError(
                "Browser applications are enabled but candidate_email is missing."
            )

        if not settings.candidate_phone:
            raise RuntimeError(
                "Browser applications are enabled but candidate_phone is missing."
            )

        if not settings.candidate_resume_path:
            raise RuntimeError(
                "Browser applications are enabled but candidate_resume_path is missing."
            )

        resume_path = Path(settings.candidate_resume_path)

        if not resume_path.is_file():
            raise RuntimeError(
                f"Candidate resume not found: {resume_path.resolve()}"
            )

        candidate = CandidateProfile(
            full_name=settings.candidate_name,
            email=settings.candidate_email,
            phone=settings.candidate_phone,
            location=settings.candidate_location,
            resume_path=str(resume_path),
            linkedin_url=settings.candidate_linkedin_url,
            github_url=settings.candidate_github_url,
            portfolio_url=settings.candidate_portfolio_url,
        )

        browser_adapter = BrowserApplicationAdapter(
            candidate=candidate,
            headless=settings.browser_headless,
            timeout_ms=settings.browser_timeout_ms,
            executable_path=settings.browser_executable_path,
        )
    else:
        browser_adapter = dry_run_adapter

    if not settings.email_enabled:
        return ApplicationService(
            email_adapter=dry_run_adapter,
            browser_adapter=browser_adapter,
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
        browser_adapter=browser_adapter,
        repository=application_repository,
    )


class ScheduledWorker(ScheduledWork):
    """Run each scheduled cycle with a fresh database session."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run_cycle(self) -> None:
        session = SessionLocal()

        try:
            cycle = build_worker_cycle(
                settings=self.settings,
                session=session,
            )
            cycle.run_cycle()
        finally:
            session.close()


def build_worker_cycle(
    settings: Settings,
    session: Session,
) -> WorkerCycle:
    """Build one worker cycle using the supplied database session."""

    client = AdzunaClient(
        app_id=settings.adzuna_app_id or "",
        app_key=settings.adzuna_app_key or "",
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

    return WorkerCycle(
        settings=settings,
        client=client,
        repository=repository,
        decision_repository=decision_repository,
        application_repository=application_repository,
        application_service=application_service,
        target_discovery=target_discovery,
    )


def run() -> None:
    """Run one complete worker cycle."""

    settings = get_settings()

    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        raise RuntimeError(
            "Adzuna credentials are not configured. "
            "Set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env."
        )

    create_tables()

    session = SessionLocal()

    try:
        cycle = build_worker_cycle(
            settings=settings,
            session=session,
        )
        cycle.run_cycle()
    finally:
        session.close()


def run_scheduled() -> None:
    """Run the worker continuously at the configured discovery interval."""

    settings = get_settings()

    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        raise RuntimeError(
            "Adzuna credentials are not configured. "
            "Set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env."
        )

    create_tables()

    scheduler_config = SchedulerConfig(
        discovery_interval_minutes=settings.scheduler_discovery_interval_minutes,
        recovery_interval_minutes=settings.scheduler_recovery_interval_minutes,
    )

    scheduler = SchedulerService(
        work=ScheduledWorker(settings),
        config=scheduler_config,
    )

    print("=" * 60)
    print("ElectroHire Intelligence - Scheduled Worker")
    print("=" * 60)
    print(
        "Discovery interval: "
        f"{scheduler_config.discovery_interval_minutes} minutes"
    )
    print("Press Ctrl+C to stop.")
    print()

    try:
        scheduler.run_forever()
    except KeyboardInterrupt:
        print()
        print("Stopping scheduled worker...")
        scheduler.stop()


if __name__ == "__main__":
    run()
