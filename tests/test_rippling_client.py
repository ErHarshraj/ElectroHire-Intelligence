import json

import httpx
import pytest

from packages.job_sources.rippling.client import RipplingClient


def test_rippling_client_builds_board_url() -> None:
    client = RipplingClient(board_slug="tylsemi")

    assert client.board_url == "https://api.rippling.com/platform/api/ats/v1/board/tylsemi/jobs"


def test_rippling_client_builds_job_url() -> None:
    client = RipplingClient(board_slug="tylsemi")

    assert (
        client.job_url("89ca06b8-ebf8-4a40-91e3-ae09f818f66a")
        == "https://ats.rippling.com/tylsemi/jobs/"
        "89ca06b8-ebf8-4a40-91e3-ae09f818f66a"
    )


def test_rippling_client_rejects_empty_board_slug() -> None:
    with pytest.raises(
        ValueError,
        match="board slug must not be empty",
    ):
        RipplingClient(board_slug="   ")


def test_rippling_client_rejects_empty_job_uuid() -> None:
    client = RipplingClient(board_slug="tylsemi")

    with pytest.raises(
        ValueError,
        match="job UUID must not be empty",
    ):
        client.job_url("   ")


def test_rippling_client_fetch_board_jobs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = [
        {
            "uuid": "job-1",
            "name": "Embedded Engineer",
            "url": "https://ats.rippling.com/tylsemi/jobs/job-1",
        },
        {
            "uuid": "job-2",
            "name": "Hardware Engineer",
            "url": "https://ats.rippling.com/tylsemi/jobs/job-2",
        },
        {
            "name": "Invalid job",
        },
        "not-a-job",
    ]

    class MockResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> list[object]:
            return payload

    def mock_get(*args: object, **kwargs: object) -> MockResponse:
        return MockResponse()

    monkeypatch.setattr(httpx, "get", mock_get)

    client = RipplingClient(board_slug="tylsemi")

    jobs = client.fetch_board_jobs()

    assert len(jobs) == 2
    assert jobs[0]["uuid"] == "job-1"
    assert jobs[1]["uuid"] == "job-2"


def test_rippling_client_rejects_non_array_board_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class MockResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, object]:
            return {"jobs": []}

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: MockResponse(),
    )

    client = RipplingClient(board_slug="tylsemi")

    with pytest.raises(
        TypeError,
        match="must be a JSON array",
    ):
        client.fetch_board_jobs()


def test_rippling_client_fetch_job_detail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_data = {
        "department": {
            "name": "RnD/Engineering",
        },
        "jobBoard": {
            "companyName": "TYLsemi, Inc.",
        },
        "jobPost": {
            "uuid": "job-1",
            "name": "Staff Embedded Firmware Engineer",
        },
        "payRangeDetails": [],
        "workLocations": ["Bengaluru, India"],
    }

    next_data = {
        "props": {
            "pageProps": {
                "apiData": api_data,
            },
        },
    }

    html = (
        "<html>"
        '<script id="__NEXT_DATA__" type="application/json">'
        f"{json.dumps(next_data)}"
        "</script>"
        "</html>"
    )

    class MockResponse:
        text = html

        def raise_for_status(self) -> None:
            pass

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: MockResponse(),
    )

    client = RipplingClient(board_slug="tylsemi")

    result = client.fetch_job_detail("job-1")

    assert result == api_data
    assert result["jobPost"]["uuid"] == "job-1"
    assert result["workLocations"] == ["Bengaluru, India"]


def test_rippling_client_rejects_missing_next_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class MockResponse:
        text = "<html><body>No data</body></html>"

        def raise_for_status(self) -> None:
            pass

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: MockResponse(),
    )

    client = RipplingClient(board_slug="tylsemi")

    with pytest.raises(
        ValueError,
        match="does not contain __NEXT_DATA__",
    ):
        client.fetch_job_detail("job-1")


def test_rippling_client_rejects_missing_job_post(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    next_data = {
        "props": {
            "pageProps": {
                "apiData": {},
            },
        },
    }

    html = f'<script id="__NEXT_DATA__" type="application/json">{json.dumps(next_data)}</script>'

    class MockResponse:
        text = html

        def raise_for_status(self) -> None:
            pass

    monkeypatch.setattr(
        httpx,
        "get",
        lambda *args, **kwargs: MockResponse(),
    )

    client = RipplingClient(board_slug="tylsemi")

    with pytest.raises(
        TypeError,
        match="missing jobPost",
    ):
        client.fetch_job_detail("job-1")
