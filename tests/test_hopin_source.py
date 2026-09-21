from unittest.mock import Mock

from packages.common.hopin_config import HopinConfig
from packages.domain.job import Job
from packages.job_sources.hopin.client import HopinClient
from packages.job_sources.hopin.source import HopinJobSource


def test_hopin_job_source_fetches_jobs() -> None:
    client = Mock(spec=HopinClient)
    client.fetch_jobs.return_value = [
        {
            "id": 101,
            "company": "Example Electronics",
            "title": "Embedded Engineer",
            "description": "Embedded systems role.",
            "location": "India",
            "work_type": "Remote",
            "industry": "Technology",
            "role_type": "Full-time",
            "job_type": "Full-time",
            "posted_at": "2026-09-20T10:00:00Z",
            "is_active": True,
        }
    ]

    config = HopinConfig(
        endpoint="jobs",
        industry="Technology",
        location="India",
        unofficial=False,
    )

    source = HopinJobSource(
        client=client,
        config=config,
    )

    jobs = list(source.fetch_jobs())

    assert len(jobs) == 1
    assert isinstance(jobs[0], Job)
    assert jobs[0].title == "Embedded Engineer"
    assert jobs[0].company == "Example Electronics"
    assert jobs[0].source == "hopin"
    assert jobs[0].source_job_id == "101"

    client.fetch_jobs.assert_called_once_with(
        industry="Technology",
        location="India",
        work_type=None,
        role_type=None,
        unofficial=False,
    )


def test_hopin_job_source_fetches_internships() -> None:
    client = Mock(spec=HopinClient)
    client.fetch_internships.return_value = [
        {
            "id": 202,
            "company": "Example Robotics",
            "title": "Embedded Systems Intern",
            "description": "Embedded internship.",
            "location": "India",
            "work_type": "On-site",
            "industry": "Technology",
            "role_type": "Internship",
            "stipend": "₹20,000/month",
            "posted_at": "2026-09-20T10:00:00Z",
            "is_active": True,
        }
    ]

    config = HopinConfig(
        endpoint="internships",
        industry="Technology",
        location="India",
        unofficial=False,
    )

    source = HopinJobSource(
        client=client,
        config=config,
    )

    jobs = list(source.fetch_jobs())

    assert len(jobs) == 1
    assert isinstance(jobs[0], Job)
    assert jobs[0].title == "Embedded Systems Intern"
    assert jobs[0].company == "Example Robotics"
    assert jobs[0].source == "hopin"
    assert jobs[0].source_job_id == "202"

    client.fetch_internships.assert_called_once_with(
        industry="Technology",
        location="India",
        work_type=None,
        role_type=None,
        unofficial=False,
    )
