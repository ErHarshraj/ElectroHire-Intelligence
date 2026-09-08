from dataclasses import dataclass, field


@dataclass(frozen=True)
class CandidateProfile:
    """Structured candidate information used by application adapters."""

    full_name: str
    email: str
    phone: str

    location: str | None = None

    resume_path: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None

    education: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)

    application_answers: dict[str, str] = field(default_factory=dict)
