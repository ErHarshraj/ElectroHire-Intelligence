from enum import Enum


class JobStatus(str, Enum):
    """Processing lifecycle state of a discovered job."""

    DISCOVERED = "discovered"
    EVALUATED = "evaluated"
    SHORTLISTED = "shortlisted"
    IGNORED = "ignored"
