from datetime import datetime, timezone

from pydantic import HttpUrl

from packages.domain.job import Job
from packages.job_sources.base import JobSource


class MockJobSource(JobSource):
    """Deterministic job source used for development and testing."""

    name = "mock"

    def fetch_jobs(self) -> list[Job]:
        return [
            Job(
                title="Embedded Hardware Engineer",
                company="Example Electronics",
                location="Bengaluru, India",
                description="Design embedded hardware and PCB systems.",
                source=self.name,
                source_job_id="MOCK-001",
                source_url=HttpUrl("https://example.com/jobs/MOCK-001"),
                employment_type="Full-time",
                experience_required="0-2 years",
                skills=["Embedded C", "PCB Design", "STM32"],
                posted_at=datetime(2026, 8, 28, tzinfo=timezone.utc),
                discovered_at=datetime(2026, 8, 28, tzinfo=timezone.utc),
            ),
            Job(
                title="PCB Design Engineer",
                company="Example Robotics",
                location="Hyderabad, India",
                description="Design multilayer PCBs for robotics products.",
                source=self.name,
                source_job_id="MOCK-002",
                source_url=HttpUrl("https://example.com/jobs/MOCK-002"),
                employment_type="Full-time",
                experience_required="0-2 years",
                skills=["PCB Design", "KiCad", "Altium"],
                posted_at=datetime(2026, 8, 28, tzinfo=timezone.utc),
                discovered_at=datetime(2026, 8, 28, tzinfo=timezone.utc),
            ),
        ]
