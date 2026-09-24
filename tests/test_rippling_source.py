from unittest.mock import Mock

from packages.job_sources.rippling.client import RipplingClient
from packages.job_sources.rippling.source import RipplingJobSource


def test_rippling_job_source_fetch_jobs() -> None:
    client = Mock(spec=RipplingClient)

    client.fetch_board_jobs.return_value = [
        {
            "uuid": "job-1",
            "name": "Embedded Engineer",
            "url": "https://ats.rippling.com/example/jobs/job-1",
        },
        {
            "uuid": "job-2",
            "name": "Hardware Engineer",
            "url": "https://ats.rippling.com/example/jobs/job-2",
        },
    ]

    client.fetch_job_detail.side_effect = [
        {
            "jobPost": {
                "uuid": "job-1",
                "name": "Embedded Engineer",
                "companyName": "Example Corp",
                "url": "https://ats.rippling.com/example/jobs/job-1",
                "workLocations": ["Bengaluru, India"],
            }
        },
        {
            "jobPost": {
                "uuid": "job-2",
                "name": "Hardware Engineer",
                "companyName": "Example Corp",
                "url": "https://ats.rippling.com/example/jobs/job-2",
                "workLocations": ["Pune, India"],
            }
        },
    ]

    source = RipplingJobSource(
        client=client,
        company_name="Example Corp",
    )

    jobs = list(source.fetch_jobs())

    assert len(jobs) == 2
    assert jobs[0].title == "Embedded Engineer"
    assert jobs[1].title == "Hardware Engineer"

    assert jobs[0].source == "rippling"
    assert jobs[1].source == "rippling"

    assert jobs[0].source_job_id == "job-1"
    assert jobs[1].source_job_id == "job-2"


def test_rippling_job_source_deduplicates_job_uuids() -> None:
    client = Mock(spec=RipplingClient)

    client.fetch_board_jobs.return_value = [
        {
            "uuid": "job-1",
            "name": "Embedded Engineer",
            "url": "https://ats.rippling.com/example/jobs/job-1",
        },
        {
            "uuid": "job-1",
            "name": "Embedded Engineer",
            "url": "https://ats.rippling.com/example/jobs/job-1",
        },
        {
            "uuid": "job-2",
            "name": "Hardware Engineer",
            "url": "https://ats.rippling.com/example/jobs/job-2",
        },
        {
            "uuid": "job-2",
            "name": "Hardware Engineer",
            "url": "https://ats.rippling.com/example/jobs/job-2",
        },
    ]

    client.fetch_job_detail.side_effect = [
        {
            "jobPost": {
                "uuid": "job-1",
                "name": "Embedded Engineer",
                "url": "https://ats.rippling.com/example/jobs/job-1",
            }
        },
        {
            "jobPost": {
                "uuid": "job-2",
                "name": "Hardware Engineer",
                "url": "https://ats.rippling.com/example/jobs/job-2",
            }
        },
    ]

    source = RipplingJobSource(
        client=client,
        company_name="Example Corp",
    )

    jobs = list(source.fetch_jobs())

    assert len(jobs) == 2
    assert client.fetch_job_detail.call_count == 2

    client.fetch_job_detail.assert_any_call("job-1")
    client.fetch_job_detail.assert_any_call("job-2")


def test_rippling_job_source_skips_records_without_uuid() -> None:
    client = Mock(spec=RipplingClient)

    client.fetch_board_jobs.return_value = [
        {
            "name": "Missing UUID",
            "url": "https://ats.rippling.com/example/jobs/missing",
        },
        {
            "uuid": "",
            "name": "Empty UUID",
        },
        {
            "uuid": "job-1",
            "name": "Valid Job",
        },
    ]

    client.fetch_job_detail.return_value = {
        "jobPost": {
            "uuid": "job-1",
            "name": "Valid Job",
            "url": "https://ats.rippling.com/example/jobs/job-1",
        }
    }

    source = RipplingJobSource(
        client=client,
        company_name="Example Corp",
    )

    jobs = list(source.fetch_jobs())

    assert len(jobs) == 1
    assert jobs[0].source_job_id == "job-1"
    client.fetch_job_detail.assert_called_once_with("job-1")


def test_rippling_job_source_uses_configured_company() -> None:
    client = Mock(spec=RipplingClient)

    client.fetch_board_jobs.return_value = [
        {
            "uuid": "job-1",
            "name": "Hardware Engineer",
        }
    ]

    client.fetch_job_detail.return_value = {
        "jobPost": {
            "uuid": "job-1",
            "name": "Hardware Engineer",
            "url": "https://ats.rippling.com/example/jobs/job-1",
        }
    }

    source = RipplingJobSource(
        client=client,
        company_name="Configured Company",
    )

    jobs = list(source.fetch_jobs())

    assert jobs[0].company == "Configured Company"
