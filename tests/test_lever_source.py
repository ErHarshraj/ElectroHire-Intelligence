from unittest.mock import Mock, patch

import pytest

from packages.domain.job import Job
from packages.job_sources.career.lever import LeverJobSource
from packages.sources import SourceType


def test_lever_source_metadata() -> None:
    source = LeverJobSource(
        company_name="Palantir",
        site="palantir",
    )

    assert source.name == "lever"
    assert source.source_type == SourceType.JOB
    assert source.company_name == "Palantir"
    assert source.site == "palantir"
    assert source.board_url == (
        "https://api.lever.co/v0/postings/palantir"
    )


def test_lever_source_rejects_invalid_configuration() -> None:
    with pytest.raises(ValueError):
        LeverJobSource(company_name="", site="palantir")

    with pytest.raises(ValueError):
        LeverJobSource(company_name="Palantir", site="")

    with pytest.raises(ValueError):
        LeverJobSource(
            company_name="Palantir",
            site="palantir",
            page_size=0,
        )


def test_lever_source_parses_job() -> None:
    source = LeverJobSource(
        company_name="Example Electronics",
        site="example-electronics",
    )

    payload = [
        {
            "id": "lever-job-123",
            "text": "Embedded Hardware Engineer",
            "categories": {
                "location": "Bengaluru, India",
                "commitment": "Full-time",
                "team": "Engineering",
                "department": "Hardware",
                "allLocations": ["Bengaluru, India"],
            },
            "descriptionPlain": (
                "Design embedded hardware systems and prototypes."
            ),
            "hostedUrl": (
                "https://jobs.lever.co/example-electronics/lever-job-123"
            ),
            "applyUrl": (
                "https://jobs.lever.co/example-electronics/"
                "lever-job-123/apply"
            ),
            "workplaceType": "hybrid",
        }
    ]

    response = Mock()
    response.json.return_value = payload

    with patch(
        "packages.job_sources.career.lever.httpx.get",
        return_value=response,
    ) as mock_get:
        jobs = list(source.fetch_jobs())

    mock_get.assert_called_once()

    assert len(jobs) == 1

    job = jobs[0]

    assert isinstance(job, Job)
    assert job.title == "Embedded Hardware Engineer"
    assert job.company == "Example Electronics"
    assert job.location == "Bengaluru, India"
    assert job.description == (
        "Design embedded hardware systems and prototypes."
    )
    assert job.source == "lever"
    assert job.source_job_id == "lever-job-123"
    assert str(job.source_url) == (
        "https://jobs.lever.co/example-electronics/lever-job-123"
    )
    assert job.employment_type == "Full-time"
    assert job.experience_required is None
    assert job.skills == []
    assert job.posted_at is None


def test_lever_source_paginates() -> None:
    source = LeverJobSource(
        company_name="Example Electronics",
        site="example-electronics",
        page_size=2,
    )

    first_payload = [
        {
            "id": "job-1",
            "text": "Hardware Engineer",
            "categories": {"location": "India"},
            "descriptionPlain": "Hardware design.",
            "hostedUrl": "https://jobs.lever.co/example/job-1",
        },
        {
            "id": "job-2",
            "text": "Embedded Engineer",
            "categories": {"location": "India"},
            "descriptionPlain": "Embedded systems.",
            "hostedUrl": "https://jobs.lever.co/example/job-2",
        },
    ]

    second_payload = [
        {
            "id": "job-3",
            "text": "PCB Engineer",
            "categories": {"location": "India"},
            "descriptionPlain": "PCB design.",
            "hostedUrl": "https://jobs.lever.co/example/job-3",
        },
    ]

    first_response = Mock()
    first_response.json.return_value = first_payload

    second_response = Mock()
    second_response.json.return_value = second_payload

    with patch(
        "packages.job_sources.career.lever.httpx.get",
        side_effect=[first_response, second_response],
    ) as mock_get:
        jobs = list(source.fetch_jobs())

    assert [job.source_job_id for job in jobs] == [
        "job-1",
        "job-2",
        "job-3",
    ]

    assert mock_get.call_count == 2

    assert mock_get.call_args_list[0].kwargs["params"] == {
        "skip": 0,
        "limit": 2,
        "mode": "json",
    }

    assert mock_get.call_args_list[1].kwargs["params"] == {
        "skip": 2,
        "limit": 2,
        "mode": "json",
    }


def test_lever_source_rejects_invalid_payload() -> None:
    source = LeverJobSource(
        company_name="Example Electronics",
        site="example-electronics",
    )

    response = Mock()
    response.json.return_value = {"jobs": []}

    with patch(
        "packages.job_sources.career.lever.httpx.get",
        return_value=response,
    ):
        with pytest.raises(TypeError, match="Lever postings must be a list"):
            list(source.fetch_jobs())


def test_lever_source_rejects_invalid_posting() -> None:
    source = LeverJobSource(
        company_name="Example Electronics",
        site="example-electronics",
    )

    response = Mock()
    response.json.return_value = ["invalid"]

    with patch(
        "packages.job_sources.career.lever.httpx.get",
        return_value=response,
    ):
        with pytest.raises(TypeError, match="Lever posting must be an object"):
            list(source.fetch_jobs())
