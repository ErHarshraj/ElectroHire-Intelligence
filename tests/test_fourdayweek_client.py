import httpx
import pytest

from packages.job_sources.fourdayweek.client import FourDayWeekClient


def test_fetch_jobs_single_page(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, object]:
            return {
                "page": 1,
                "limit": 2,
                "total": 2,
                "has_more": False,
                "data": [
                    {
                        "id": "job-1",
                        "title": "Embedded Engineer",
                    },
                    {
                        "id": "job-2",
                        "title": "Hardware Engineer",
                    },
                ],
            }

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        captured["url"] = url
        captured["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr(httpx, "get", fake_get)

    jobs = FourDayWeekClient().fetch_jobs(limit=2)

    assert captured["url"] == "https://4dayweek.io/api/v2/jobs"

    kwargs = captured["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["params"] == {
        "page": 1,
        "limit": 2,
    }

    assert jobs == [
        {
            "id": "job-1",
            "title": "Embedded Engineer",
        },
        {
            "id": "job-2",
            "title": "Hardware Engineer",
        },
    ]


def test_fetch_jobs_follows_pagination(monkeypatch) -> None:
    requests: list[dict[str, object]] = []

    responses = [
        {
            "page": 1,
            "limit": 2,
            "total": 3,
            "has_more": True,
            "data": [
                {
                    "id": "job-1",
                    "title": "Embedded Engineer",
                },
                {
                    "id": "job-2",
                    "title": "PCB Engineer",
                },
            ],
        },
        {
            "page": 2,
            "limit": 2,
            "total": 3,
            "has_more": False,
            "data": [
                {
                    "id": "job-3",
                    "title": "Hardware Engineer",
                },
            ],
        },
    ]

    class FakeResponse:
        def __init__(self, payload: dict[str, object]) -> None:
            self.payload = payload

        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, object]:
            return self.payload

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        requests.append(kwargs)
        return FakeResponse(responses[len(requests) - 1])

    monkeypatch.setattr(httpx, "get", fake_get)

    jobs = FourDayWeekClient().fetch_jobs(limit=2)

    assert len(requests) == 2
    assert requests[0]["params"] == {
        "page": 1,
        "limit": 2,
    }
    assert requests[1]["params"] == {
        "page": 2,
        "limit": 2,
    }

    assert jobs == [
        {
            "id": "job-1",
            "title": "Embedded Engineer",
        },
        {
            "id": "job-2",
            "title": "PCB Engineer",
        },
        {
            "id": "job-3",
            "title": "Hardware Engineer",
        },
    ]


@pytest.mark.parametrize("limit", [0, -1, 101, 200])
def test_fetch_jobs_rejects_invalid_limit(limit: int) -> None:
    with pytest.raises(ValueError, match="between 1 and 100"):
        FourDayWeekClient().fetch_jobs(limit=limit)


def test_fetch_jobs_rejects_non_object_response(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> list[dict[str, object]]:
            return []

    monkeypatch.setattr(
        httpx,
        "get",
        lambda url, **kwargs: FakeResponse(),
    )

    with pytest.raises(TypeError, match="JSON object"):
        FourDayWeekClient().fetch_jobs()


def test_fetch_jobs_rejects_missing_data(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, object]:
            return {
                "page": 1,
                "limit": 100,
                "total": 0,
                "has_more": False,
            }

    monkeypatch.setattr(
        httpx,
        "get",
        lambda url, **kwargs: FakeResponse(),
    )

    with pytest.raises(TypeError, match="data list"):
        FourDayWeekClient().fetch_jobs()


def test_fetch_jobs_rejects_invalid_has_more(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, object]:
            return {
                "page": 1,
                "limit": 100,
                "total": 1,
                "has_more": "false",
                "data": [
                    {
                        "id": "job-1",
                        "title": "Embedded Engineer",
                    }
                ],
            }

    monkeypatch.setattr(
        httpx,
        "get",
        lambda url, **kwargs: FakeResponse(),
    )

    with pytest.raises(TypeError, match="boolean has_more"):
        FourDayWeekClient().fetch_jobs()


def test_fetch_jobs_filters_invalid_records(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, object]:
            return {
                "page": 1,
                "limit": 100,
                "total": 4,
                "has_more": False,
                "data": [
                    {
                        "id": "valid",
                        "title": "Embedded Engineer",
                    },
                    {
                        "id": "missing-title",
                    },
                    {
                        "title": "Missing ID",
                    },
                    "invalid-record",
                ],
            }

    monkeypatch.setattr(
        httpx,
        "get",
        lambda url, **kwargs: FakeResponse(),
    )

    jobs = FourDayWeekClient().fetch_jobs()

    assert jobs == [
        {
            "id": "valid",
            "title": "Embedded Engineer",
        }
    ]


def test_fetch_jobs_propagates_http_error(monkeypatch) -> None:
    def fake_get(url: str, **kwargs: object) -> httpx.Response:
        request = httpx.Request("GET", url)
        return httpx.Response(
            500,
            request=request,
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(httpx.HTTPStatusError):
        FourDayWeekClient().fetch_jobs()
