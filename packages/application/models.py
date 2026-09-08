from dataclasses import dataclass
from enum import Enum


class ApplicationMethod(str, Enum):
    """Supported mechanisms for submitting a job application."""

    EMAIL = "email"
    BROWSER = "browser"


class ApplicationStatus(str, Enum):
    """Lifecycle state of an application attempt."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    PAUSED = "paused"
    FAILED = "failed"
    ALREADY_SUBMITTED = "already_submitted"


@dataclass(frozen=True)
class ApplicationRequest:
    """Information required to submit an application."""

    source: str
    source_job_id: str
    job_title: str
    company: str
    application_method: ApplicationMethod
    apply_url: str | None = None
    recruiter_email: str | None = None


@dataclass(frozen=True)
class ApplicationResult:
    """Result returned by an application adapter."""

    status: ApplicationStatus
    method: ApplicationMethod
    message: str
    external_reference: str | None = None
