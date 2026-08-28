from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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
