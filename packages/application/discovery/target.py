from dataclasses import dataclass
from enum import Enum


class ApplicationTargetMethod(str, Enum):
    """Available ways to apply for a job."""

    EMAIL = "email"
    BROWSER = "browser"
    NONE = "none"


@dataclass(frozen=True)
class ApplicationTarget:
    """Normalized destination through which a job can be applied."""

    method: ApplicationTargetMethod
    apply_url: str | None = None
    recruiter_email: str | None = None
    reason: str = ""
