from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class Job(BaseModel):
    """Canonical internal representation of a job opportunity."""

    title: str
    company: str

    location: str | None = None
    description: str | None = None

    source: str
    source_job_id: str | None = None
    source_url: HttpUrl

    employment_type: str | None = None
    experience_required: str | None = None

    skills: list[str] = Field(default_factory=list)

    posted_at: datetime | None = None
    discovered_at: datetime

    is_active: bool = True
