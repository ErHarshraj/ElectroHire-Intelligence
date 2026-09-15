from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from packages.job_sources.career.base import CareerSiteJobSource
from packages.job_sources.career.greenhouse import GreenhouseJobSource
from packages.sources import SourceType


def test_greenhouse_source_metadata() -> None:
    source = GreenhouseJobSource(
        company_name="Example Electronics",
        board_token="example-token",
    )

    assert isinstance(source, CareerSiteJobSource)
    assert source.name == "greenhouse"
    assert source.source_type == SourceType.JOB
    assert source.company_name == "Example Electronics"
    assert source.board_token == "example-token"
    assert (
        source.board_url
        == "https://boards-api.greenhouse.io/v1/boards/"
        "example-token/jobs"
    )


def test_greenhouse_source_rejects_empty_company_name() -> None:
    with pytest.raises(
        ValueError,
        match="company_name must not be empty",
    ):
        GreenhouseJobSource(
            company_name="   ",
            board_token="example-token",
        )


def test_greenhouse_source_rejects_empty_board_token() -> None:
    with pytest.raises(
        ValueError,
        match="board_token must not be empty",
    ):
        GreenhouseJobSource(
            company_name="Example Electronics",
            board_token="   ",
        )


def test_greenhouse_source_parses_jobs() -> None:
    payload = {
        "jobs": [
            {
                "id": 12345,
                "title": "Embedded Hardware Engineer",
                "location": {
                    "name": "Bengaluru, India",
                },
                "content": (
                    "<p>Design embedded hardware and PCB systems.</p>"
                ),
                "updated_at": "2026-08-28T10:30:00Z",
                "absolute_url": (
                    "https://boards.greenhouse.io/example/jobs/12345"
                ),
            }
        ]
    }

    response = Mock()
    response.json.return_value = payload

    source = GreenhouseJobSource(
        company_name="Example Electronics",
        board_token="example-token",
    )

    with patch(
        "packages.job_sources.career.greenhouse.httpx.get",
        return_value=response,
    ) as mock_get:
        jobs = list(source.fetch_jobs())

    mock_get.assert_called_once_with(
        source.board_url,
        params={"content": "true"},
        timeout=15.0,
    )

    response.raise_for_status.assert_called_once()

    assert len(jobs) == 1

    job = jobs[0]

    assert job.title == "Embedded Hardware Engineer"
    assert job.company == "Example Electronics"
    assert job.location == "Bengaluru, India"
    assert (
        job.description
        == "<p>Design embedded hardware and PCB systems.</p>"
    )
    assert job.source == "greenhouse"
    assert job.source_job_id == "12345"
    assert str(job.source_url) == (
        "https://boards.greenhouse.io/example/jobs/12345"
    )
    assert job.skills == []
    assert job.posted_at == datetime(
        2026,
        8,
        28,
        10,
        30,
        tzinfo=timezone.utc,
    )
    assert job.discovered_at.tzinfo is not None


def test_greenhouse_source_handles_missing_jobs() -> None:
    response = Mock()
    response.json.return_value = {}

    source = GreenhouseJobSource(
        company_name="Example Electronics",
        board_token="example-token",
    )

    with patch(
        "packages.job_sources.career.greenhouse.httpx.get",
        return_value=response,
    ):
        jobs = list(source.fetch_jobs())

    assert jobs == []


def test_greenhouse_source_rejects_invalid_jobs_payload() -> None:
    response = Mock()
    response.json.return_value = {
        "jobs": "not-a-list",
    }

    source = GreenhouseJobSource(
        company_name="Example Electronics",
        board_token="example-token",
    )

    with patch(
        "packages.job_sources.career.greenhouse.httpx.get",
        return_value=response,
    ):
        with pytest.raises(
            TypeError,
            match="Greenhouse jobs must be a list",
        ):
            list(source.fetch_jobs())


def test_greenhouse_source_rejects_invalid_job_item() -> None:
    response = Mock()
    response.json.return_value = {
        "jobs": ["not-an-object"],
    }

    source = GreenhouseJobSource(
        company_name="Example Electronics",
        board_token="example-token",
    )

    with patch(
        "packages.job_sources.career.greenhouse.httpx.get",
        return_value=response,
    ):
        with pytest.raises(
            TypeError,
            match="Greenhouse job must be an object",
        ):
            list(source.fetch_jobs())


def test_greenhouse_datetime_parser_handles_missing_value() -> None:
    assert GreenhouseJobSource._parse_datetime(None) is None
    assert GreenhouseJobSource._parse_datetime("") is None


def test_greenhouse_datetime_parser_handles_iso_datetime() -> None:
    result = GreenhouseJobSource._parse_datetime(
        "2026-08-28T10:30:00Z"
    )

    assert result == datetime(
        2026,
        8,
        28,
        10,
        30,
        tzinfo=timezone.utc,
    )
