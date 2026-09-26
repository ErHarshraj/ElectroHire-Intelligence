from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class CareerApplicationStatus(str, Enum):
    """Lifecycle state of a user's career application."""

    SHORTLISTED = "shortlisted"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    TECHNICAL = "technical"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class InvalidCareerApplicationTransition(ValueError):
    """Raised when an invalid career application status transition is requested."""


CAREER_APPLICATION_TRANSITIONS: dict[
    CareerApplicationStatus,
    frozenset[CareerApplicationStatus],
] = {
    CareerApplicationStatus.SHORTLISTED: frozenset(
        {
            CareerApplicationStatus.APPLIED,
            CareerApplicationStatus.WITHDRAWN,
        }
    ),
    CareerApplicationStatus.APPLIED: frozenset(
        {
            CareerApplicationStatus.SCREENING,
            CareerApplicationStatus.REJECTED,
            CareerApplicationStatus.WITHDRAWN,
            CareerApplicationStatus.EXPIRED,
        }
    ),
    CareerApplicationStatus.SCREENING: frozenset(
        {
            CareerApplicationStatus.INTERVIEW,
            CareerApplicationStatus.REJECTED,
            CareerApplicationStatus.WITHDRAWN,
            CareerApplicationStatus.EXPIRED,
        }
    ),
    CareerApplicationStatus.INTERVIEW: frozenset(
        {
            CareerApplicationStatus.TECHNICAL,
            CareerApplicationStatus.OFFER,
            CareerApplicationStatus.REJECTED,
            CareerApplicationStatus.WITHDRAWN,
            CareerApplicationStatus.EXPIRED,
        }
    ),
    CareerApplicationStatus.TECHNICAL: frozenset(
        {
            CareerApplicationStatus.OFFER,
            CareerApplicationStatus.REJECTED,
            CareerApplicationStatus.WITHDRAWN,
            CareerApplicationStatus.EXPIRED,
        }
    ),
    CareerApplicationStatus.OFFER: frozenset(),
    CareerApplicationStatus.REJECTED: frozenset(),
    CareerApplicationStatus.WITHDRAWN: frozenset(),
    CareerApplicationStatus.EXPIRED: frozenset(),
}


def validate_career_application_transition(
    current: CareerApplicationStatus,
    target: CareerApplicationStatus,
) -> None:
    """Validate a career application status transition."""

    if current == target:
        return

    allowed = CAREER_APPLICATION_TRANSITIONS[current]

    if target not in allowed:
        raise InvalidCareerApplicationTransition(
            f"invalid career application transition: "
            f"{current.value} -> {target.value}"
        )


@dataclass(frozen=True)
class CareerApplicationRecord:
    """Persisted career-level application tracking record."""

    job_id: int
    status: CareerApplicationStatus
    id: int | None = None
    application_url: str | None = None
    applied_at: datetime | None = None
    notes: str = ""
    last_followup_at: datetime | None = None
    next_followup_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
