from __future__ import annotations

from packages.job_sources.workable.client import WorkableClient
from packages.job_sources.workable.source import WorkableJobSource


def test_workable_job_source_fetch_jobs(
    monkeypatch,
) -> None:
    payload = [
        {
            "title": "Embedded Systems Engineer",
            "shortcode": "EMB123",
            "url": "https://apply.workable.com/j/EMB123",
            "description": "<p>Embedded role.</p>",
            "location": "Bengaluru, India",
            "employment_type": "Full-time",
            "experience": "0-2 years",
        },
        {
            "title": "Hardware Design Engineer",
            "shortcode": "HW123",
            "url": "https://apply.workable.com/j/HW123",
            "description": "<p>Hardware role.</p>",
            "location": "Pune, India",
            "employment_type": "Full-time",
            "experience": "1-3 years",
        },
    ]

    def fake_fetch_jobs(self) -> list[dict]:
        return payload

    monkeypatch.setattr(
        WorkableClient,
        "fetch_jobs",
        fake_fetch_jobs,
    )

    client = WorkableClient(account_slug="example")

    source = WorkableJobSource(
        client=client,
        company_name="Example Electronics",
    )

    jobs = list(source.fetch_jobs())

    assert len(jobs) == 2

    assert jobs[0].title == "Embedded Systems Engineer"
    assert jobs[0].company == "Example Electronics"
    assert jobs[0].source == "workable"
    assert jobs[0].source_job_id == "EMB123"

    assert jobs[1].title == "Hardware Design Engineer"
    assert jobs[1].source_job_id == "HW123"


def test_workable_job_source_uses_configured_company(
    monkeypatch,
) -> None:
    def fake_fetch_jobs(self) -> list[dict]:
        return [
            {
                "title": "Electronics Engineer",
                "shortcode": "ELEC123",
                "url": "https://apply.workable.com/j/ELEC123",
            }
        ]

    monkeypatch.setattr(
        WorkableClient,
        "fetch_jobs",
        fake_fetch_jobs,
    )

    source = WorkableJobSource(
        client=WorkableClient(account_slug="example"),
        company_name="Configured Company",
    )

    jobs = list(source.fetch_jobs())

    assert len(jobs) == 1
    assert jobs[0].company == "Configured Company"
