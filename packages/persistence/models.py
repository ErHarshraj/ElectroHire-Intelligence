from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from packages.domain.job_status import JobStatus


class Base(DeclarativeBase):
    pass


class JobModel(Base):
    __tablename__ = "jobs"

    __table_args__ = (
        UniqueConstraint(
            "source",
            "source_job_id",
            name="uq_jobs_source_source_job_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String(255))
    company: Mapped[str] = mapped_column(String(255))

    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    source: Mapped[str] = mapped_column(String(100))
    source_job_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source_url: Mapped[str] = mapped_column(String(2048))

    employment_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    experience_required: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    skills: Mapped[str] = mapped_column(Text, default="")

    posted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )

    is_active: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(String(50), default=JobStatus.DISCOVERED.value)


class JobDecisionModel(Base):
    __tablename__ = "job_decisions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    relevance_score: Mapped[float] = mapped_column(
        nullable=False,
    )

    ranking_score: Mapped[float] = mapped_column(
        nullable=False,
    )

    priority: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    reasons: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class ApplicationModel(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
    )

    method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    apply_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    recruiter_email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    external_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

class ApplicationApprovalModel(Base):
    __tablename__ = "application_approvals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_job_id: Mapped[str] = mapped_column(String(255), nullable=False)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)

    method: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    apply_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    recruiter_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class WorkerRunModel(Base):
    __tablename__ = "worker_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    success: Mapped[bool] = mapped_column(nullable=False)

    queries_processed: Mapped[int] = mapped_column(nullable=False)
    new_jobs: Mapped[int] = mapped_column(nullable=False)
    evaluated_jobs: Mapped[int] = mapped_column(nullable=False)
    ignored_jobs: Mapped[int] = mapped_column(nullable=False)

    apply_decisions: Mapped[int] = mapped_column(nullable=False)
    targets_found: Mapped[int] = mapped_column(nullable=False)
    no_target: Mapped[int] = mapped_column(nullable=False)
    submitted: Mapped[int] = mapped_column(nullable=False)
    pending: Mapped[int] = mapped_column(nullable=False)
    failed: Mapped[int] = mapped_column(nullable=False)
    paused: Mapped[int] = mapped_column(nullable=False)
    already_submitted: Mapped[int] = mapped_column(nullable=False)

    recovery_candidates: Mapped[int] = mapped_column(nullable=False)
    recovery_submitted: Mapped[int] = mapped_column(nullable=False)
    recovery_failed: Mapped[int] = mapped_column(nullable=False)
    recovery_paused: Mapped[int] = mapped_column(nullable=False)
    recovery_skipped: Mapped[int] = mapped_column(nullable=False)

    error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class CareerApplicationModel(Base):
    __tablename__ = "career_applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
        unique=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    application_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    notes: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    last_followup_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    next_followup_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class CandidateProfileModel(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    resume_path: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    linkedin_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    github_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    portfolio_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    education: Mapped[str] = mapped_column(
        Text,
        default="[]",
        nullable=False,
    )

    skills: Mapped[str] = mapped_column(
        Text,
        default="[]",
        nullable=False,
    )

    projects: Mapped[str] = mapped_column(
        Text,
        default="[]",
        nullable=False,
    )

    application_answers: Mapped[str] = mapped_column(
        Text,
        default="{}",
        nullable=False,
    )

    target_roles: Mapped[str] = mapped_column(
        Text,
        default="[]",
        nullable=False,
    )

    role_families: Mapped[str] = mapped_column(
        Text,
        default="[]",
        nullable=False,
    )

    skill_families: Mapped[str] = mapped_column(
        Text,
        default="[]",
        nullable=False,
    )

    domain_families: Mapped[str] = mapped_column(
        Text,
        default="[]",
        nullable=False,
    )

    experience_keywords: Mapped[str] = mapped_column(
        Text,
        default="[]",
        nullable=False,
    )
