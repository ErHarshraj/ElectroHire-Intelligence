from unittest.mock import Mock

import httpx
import pytest

from packages.job_sources.ayla.client import AylaClient


def make_response(data: dict) -> Mock:
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = data
    return response


def test_fetch_jobs_paginates() -> None:
    responses = [
        make_response(
            {
                "jobs": [
                    {
                        "id": "job-1",
                        "title": "Hardware Engineer",
                    },
                    {
                        "id": "job-2",
                        "title": "Embedded Engineer",
                    },
                ],
                "pagination": {
                    "limit": 2,
                    "offset": 0,
                    "page": 0,
                    "total": 3,
                },
            }
        ),
        make_response(
            {
                "jobs": [
                    {
                        "id": "job-3",
                        "title": "PCB Engineer",
                    },
                ],
                "pagination": {
                    "limit": 2,
                    "offset": 2,
                    "page": 1,
                    "total": 3,
                },
            }
        ),
    ]

    calls: list[dict] = []

    def mock_get(
        url: str,
        *,
        params: dict,
        timeout: float,
        headers: dict,
    ) -> Mock:
        calls.append(
            {
                "url": url,
                "params": params,
                "timeout": timeout,
                "headers": headers,
            }
        )

        return responses[len(calls) - 1]

    original_get = httpx.get
    httpx.get = mock_get

    try:
        client = AylaClient()

        jobs = client.fetch_jobs(
            query="electronics",
            limit=2,
        )
    finally:
        httpx.get = original_get

    assert len(jobs) == 3
    assert [job["id"] for job in jobs] == [
        "job-1",
        "job-2",
        "job-3",
    ]

    assert len(calls) == 2

    assert calls[0]["params"] == {
        "search": "electronics",
        "limit": 2,
        "page": 0,
    }

    assert calls[1]["params"] == {
        "search": "electronics",
        "limit": 2,
        "page": 1,
    }


def test_fetch_jobs_rejects_empty_query() -> None:
    client = AylaClient()

    with pytest.raises(ValueError, match="query must not be empty"):
        client.fetch_jobs(query="   ")


@pytest.mark.parametrize("limit", [0, 101])
def test_fetch_jobs_rejects_invalid_limit(limit: int) -> None:
    client = AylaClient()

    with pytest.raises(ValueError, match="limit must be between 1 and 100"):
        client.fetch_jobs(
            query="electronics",
            limit=limit,
        )


def test_fetch_jobs_rejects_non_object_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = make_response(["not", "an", "object"])

    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response)

    client = AylaClient()

    with pytest.raises(
        TypeError,
        match="response must be a JSON object",
    ):
        client.fetch_jobs(query="electronics")


def test_fetch_jobs_rejects_missing_jobs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = make_response(
        {
            "pagination": {
                "limit": 100,
                "offset": 0,
                "page": 0,
                "total": 0,
            }
        }
    )

    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response)

    client = AylaClient()

    with pytest.raises(
        TypeError,
        match="must contain a jobs list",
    ):
        client.fetch_jobs(query="electronics")


def test_fetch_jobs_rejects_missing_pagination(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = make_response(
        {
            "jobs": [],
        }
    )

    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response)

    client = AylaClient()

    with pytest.raises(
        TypeError,
        match="pagination metadata",
    ):
        client.fetch_jobs(query="electronics")


def test_fetch_jobs_rejects_invalid_total(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = make_response(
        {
            "jobs": [],
            "pagination": {
                "limit": 100,
                "offset": 0,
                "page": 0,
                "total": "100",
            },
        }
    )

    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response)

    client = AylaClient()

    with pytest.raises(
        TypeError,
        match="integer total",
    ):
        client.fetch_jobs(query="electronics")


def test_fetch_jobs_rejects_invalid_offset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = make_response(
        {
            "jobs": [],
            "pagination": {
                "limit": 100,
                "offset": "0",
                "page": 0,
                "total": 0,
            },
        }
    )

    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response)

    client = AylaClient()

    with pytest.raises(
        TypeError,
        match="integer offset",
    ):
        client.fetch_jobs(query="electronics")


def test_fetch_jobs_skips_invalid_records(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = make_response(
        {
            "jobs": [
                {
                    "id": "job-1",
                    "title": "Hardware Engineer",
                },
                {
                    "id": "missing-title",
                },
                {
                    "title": "Missing ID",
                },
                "invalid",
            ],
            "pagination": {
                "limit": 100,
                "offset": 0,
                "page": 0,
                "total": 4,
            },
        }
    )

    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response)

    client = AylaClient()

    jobs = client.fetch_jobs(query="electronics")

    assert jobs == [
        {
            "id": "job-1",
            "title": "Hardware Engineer",
        }
    ]


def test_fetch_jobs_stops_on_empty_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = make_response(
        {
            "jobs": [],
            "pagination": {
                "limit": 100,
                "offset": 0,
                "page": 0,
                "total": 10,
            },
        }
    )

    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response)

    client = AylaClient()

    assert client.fetch_jobs(query="electronics") == []


def test_fetch_jobs_raises_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = Mock()
    response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "server error",
        request=Mock(),
        response=Mock(),
    )

    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: response)

    client = AylaClient()

    with pytest.raises(httpx.HTTPStatusError):
        client.fetch_jobs(query="electronics")
