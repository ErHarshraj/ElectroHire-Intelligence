"""
Domain models for company and startup opportunity discovery.
"""

from dataclasses import dataclass
from enum import Enum


class OpportunityType(str, Enum):
    """Type of engineering opportunity."""

    ADVERTISED_ROLE = "advertised_role"
    PROACTIVE_OUTREACH = "proactive_outreach"
    FUTURE_OPPORTUNITY = "future_opportunity"


class OpportunityStatus(str, Enum):
    """Lifecycle status of an opportunity."""

    DISCOVERED = "discovered"
    REVIEW = "review"
    APPROVED = "approved"
    IGNORED = "ignored"
    CONTACTED = "contacted"
    CLOSED = "closed"


class ContactMethod(str, Enum):
    """Potential method for contacting the company."""

    JOB_PORTAL = "job_portal"
    CAREERS_PAGE = "careers_page"
    EMAIL = "email"
    DIRECT_CONTACT = "direct_contact"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Company:
    """A company that may represent a career opportunity."""

    name: str
    website: str | None = None
    location: str | None = None
    industry: str | None = None
    founded_year: int | None = None
    stage: str | None = None
    size: str | None = None
    signals: tuple[str, ...] = ()


@dataclass(frozen=True)
class Opportunity:
    """
    A potential career opportunity associated with a company.

    An opportunity does not require an advertised job.
    """

    company: Company
    opportunity_type: OpportunityType

    title: str | None = None
    description: str | None = None

    advertised_job_id: str | None = None

    contact_method: ContactMethod = ContactMethod.UNKNOWN
    contact_target: str | None = None

    evidence: tuple[str, ...] = ()

    status: OpportunityStatus = OpportunityStatus.DISCOVERED


@dataclass(frozen=True)
class OpportunitySignals:
    """
    Evidence used to score a company opportunity.

    Scores are supplied by discovery/matching components.
    This model deliberately does not perform candidate matching itself.
    """

    technical_domain_fit: float = 0.0
    candidate_skill_fit: float = 0.0
    hardware_product_evidence: float = 0.0
    growth_signal: float = 0.0
    engineering_team_signal: float = 0.0
    location_fit: float = 0.0
    contactability: float = 0.0


@dataclass(frozen=True)
class OpportunityScore:
    """Result of evaluating an opportunity."""

    score: float
    band: str
    reasons: tuple[str, ...]
