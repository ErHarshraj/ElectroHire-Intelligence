from pydantic import BaseModel, Field, HttpUrl


class Company(BaseModel):
    name: str
    description: str | None = None

    website_url: HttpUrl | None = None
    careers_url: HttpUrl | None = None

    industry: str | None = None
    location: str | None = None

    employee_count: int | None = None
    is_startup: bool = False

    technologies: list[str] = Field(default_factory=list)
    discovered_from: list[str] = Field(default_factory=list)
