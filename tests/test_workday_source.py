from datetime import timezone

import httpx
import pytest

from packages.common.workday_config import parse_workday_sources
from packages.job_sources.workday.client import WorkdayClient
from packages.job_sources.workday.parser import parse_workday_job
from packages.job_sources.workday.source import WorkdayJobSource


def test_parse_workday_sources() -> None:
    configs = parse_workday_sources(
        [
            "analogdevices|https://analogdevices.wd1.myworkdayjobs.com"
            "|External|Analog Devices|10"
        ]
    )

    assert len(configs) == 1
    assert configs[0].tenant == "analogdevices"
    assert configs[0].base_url == (
        "https://analogdevices.wd1.myworkdayjobs.com"
    )
    assert configs[0].site == "External"
    assert configs[0].company_name == "Analog Devices"
    assert configs[0].batches == 10


@pytest.mark.parametrize(
    "value",
    [
        "analogdevices|External|Analog Devices|10",
        "analogdevices|https://analogdevices.wd1.myworkdayjobs.com"
        "|External|Analog Devices|0",
        "analogdevices|https://analogdevices.wd1.myworkdayjobs.com"
        "|External|Analog Devices|101",
        "analogdevices|ftp://analogdevices.example.com"
        "|External|Analog Devices|1",
    ],
)
def test_parse_workday_sources_rejects_invalid_values(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        parse_workday_sources([value])


def test_workday_client_fetch_jobs_uses_offset_pagination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[tuple[str, dict]] = []

    def fake_post(
        url: str,
        *,
        json: dict,
        timeout: float,
        headers: dict[str, str],
    ) -> httpx.Response:
        requests.append((url, json))

        offset = json["offset"]

        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "jobPostings": [
                    {
                        "title": f"Job {offset}",
                        "externalPath": f"/job/example-{offset}",
                    }
                ]
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    client = WorkdayClient(
        base_url="https://analogdevices.wd1.myworkdayjobs.com",
        tenant="analogdevices",
        site="External",
    )

    jobs = client.fetch_jobs(batches=3)

    assert len(jobs) == 3
    assert [request[1]["offset"] for request in requests] == [
        0,
        20,
        40,
    ]
    assert all(request[1]["limit"] == 20 for request in requests)
    assert all(request[1]["searchText"] == "" for request in requests)


def test_workday_client_stops_on_empty_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    offsets: list[int] = []

    def fake_post(
        url: str,
        *,
        json: dict,
        timeout: float,
        headers: dict[str, str],
    ) -> httpx.Response:
        offsets.append(json["offset"])

        if json["offset"] == 20:
            return httpx.Response(
                200,
                request=httpx.Request("POST", url),
                json={"jobPostings": []},
            )

        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "jobPostings": [
                    {
                        "title": "Embedded Systems Engineer",
                        "externalPath": "/job/example",
                    }
                ]
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    client = WorkdayClient(
        base_url="https://analogdevices.wd1.myworkdayjobs.com",
        tenant="analogdevices",
        site="External",
    )

    jobs = client.fetch_jobs(batches=5)

    assert len(jobs) == 1
    assert offsets == [0, 20]


def test_workday_client_filters_invalid_summary_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(
        url: str,
        *,
        json: dict,
        timeout: float,
        headers: dict[str, str],
    ) -> httpx.Response:
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "jobPostings": [
                    {
                        "title": "Valid Job",
                        "externalPath": "/job/valid",
                    },
                    {
                        "title": "Missing Path",
                    },
                    {
                        "externalPath": "/job/missing-title",
                    },
                    "invalid",
                ]
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    client = WorkdayClient(
        base_url="https://analogdevices.wd1.myworkdayjobs.com",
        tenant="analogdevices",
        site="External",
    )

    jobs = client.fetch_jobs()

    assert jobs == [
        {
            "title": "Valid Job",
            "externalPath": "/job/valid",
        }
    ]


def test_workday_client_fetch_job_detail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[str] = []

    def fake_get(
        url: str,
        *,
        timeout: float,
        headers: dict[str, str],
    ) -> httpx.Response:
        captured.append(url)

        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            json={
                "jobPostingInfo": {
                    "title": "Embedded Systems Engineer",
                    "jobReqId": "R254526",
                }
            },
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    client = WorkdayClient(
        base_url="https://analogdevices.wd1.myworkdayjobs.com",
        tenant="analogdevices",
        site="External",
    )

    detail = client.fetch_job_detail(
        external_path="/job/Ireland-Limerick/"
        "Embedded-Systems-Engineer_R254526"
    )

    assert detail["jobReqId"] == "R254526"
    assert captured == [
        "https://analogdevices.wd1.myworkdayjobs.com"
        "/wday/cxs/analogdevices/External"
        "/job/Ireland-Limerick/"
        "Embedded-Systems-Engineer_R254526"
    ]


def test_parse_workday_job() -> None:
    summary = {
        "title": "Embedded Systems Engineer",
        "externalPath": (
            "/job/Ireland-Limerick/"
            "Embedded-Systems-Engineer_R254526"
        ),
        "locationsText": "Ireland, Limerick",
    }

    detail = {
        "title": "Embedded Systems Engineer",
        "jobDescription": "<p>Embedded C and Python</p>",
        "location": "Ireland, Limerick",
        "jobReqId": "R254526",
        "startDate": "2025-08-12",
        "timeType": "Full time",
        "externalUrl": (
            "https://analogdevices.wd1.myworkdayjobs.com/"
            "External/job/Ireland-Limerick/"
            "Embedded-Systems-Engineer_R254526"
        ),
    }

    job = parse_workday_job(
        summary=summary,
        detail=detail,
        company_name="Analog Devices",
        source_name="workday",
        external_url=detail["externalUrl"],
    )

    assert job.title == "Embedded Systems Engineer"
    assert job.company == "Analog Devices"
    assert job.location == "Ireland, Limerick"
    assert job.description == "<p>Embedded C and Python</p>"
    assert job.source == "workday"
    assert job.source_job_id == "R254526"
    assert str(job.source_url) == detail["externalUrl"]
    assert job.employment_type == "Full time"

    # Workday's startDate is not the posting date.
    assert job.posted_at is None

    assert job.discovered_at.tzinfo == timezone.utc


def test_workday_source_fetches_and_parses_jobs() -> None:
    summary = {
        "title": "Embedded Systems Engineer",
        "externalPath": "/job/example",
    }

    detail = {
        "title": "Embedded Systems Engineer",
        "location": "Ireland, Limerick",
        "jobReqId": "R254526",
        "jobDescription": "Embedded C, Python, SPI and I2C.",
        "externalUrl": (
            "https://analogdevices.wd1.myworkdayjobs.com/"
            "External/job/example"
        ),
    }

    class FakeClient:
        base_url = "https://analogdevices.wd1.myworkdayjobs.com"

        def fetch_jobs(self, *, batches: int) -> list[dict]:
            assert batches == 1
            return [summary]

        def fetch_job_detail(
            self,
            *,
            external_path: str,
        ) -> dict:
            assert external_path == "/job/example"
            return detail

    source = WorkdayJobSource(
        client=FakeClient(),
        company_name="Analog Devices",
        batches=1,
    )

    jobs = list(source.fetch_jobs())

    assert len(jobs) == 1
    assert jobs[0].title == "Embedded Systems Engineer"
    assert jobs[0].company == "Analog Devices"
    assert jobs[0].source_job_id == "R254526"
