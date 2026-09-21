from __future__ import annotations

import httpx
import pytest

from packages.job_sources.workable.client import WorkableClient


def test_workable_client_builds_jobs_url() -> None:
    client = WorkableClient(account_slug="trocaire")

    assert client.jobs_url == (
        "https://apply.workable.com/api/v1/widget/accounts/"
        "trocaire?details=true"
    )


def test_workable_client_rejects_empty_account_slug() -> None:
    with pytest.raises(ValueError, match="account slug"):
        WorkableClient(account_slug="   ")


def test_workable_client_fetch_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "name": "Trócaire",
        "description": "Example account",
        "jobs": [
            {
                "title": "Embedded Engineer",
                "shortcode": "ABC123",
                "url": "https://apply.workable.com/j/ABC123",
            },
            {
                "title": "Hardware Engineer",
                "shortcode": "DEF456",
                "url": "https://apply.workable.com/j/DEF456",
            },
        ],
    }

    def fake_get(
        url: str,
        *,
        timeout: float,
        headers: dict[str, str],
    ) -> httpx.Response:
        assert (
            url
            == "https://apply.workable.com/api/v1/widget/accounts/"
            "trocaire?details=true"
        )
        assert timeout == 15.0
        assert headers["User-Agent"] == "ElectroHire Intelligence"

        return httpx.Response(
            200,
            json=payload,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    client = WorkableClient(account_slug="trocaire")

    jobs = client.fetch_jobs()

    assert len(jobs) == 2
    assert jobs[0]["title"] == "Embedded Engineer"
    assert jobs[1]["shortcode"] == "DEF456"


def test_workable_client_filters_invalid_jobs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "jobs": [
            {
                "title": "Valid Job",
                "shortcode": "VALID123",
                "url": "https://apply.workable.com/j/VALID123",
            },
            {
                "title": "",
                "shortcode": "NO_TITLE",
                "url": "https://apply.workable.com/j/NO_TITLE",
            },
            {
                "title": "No Shortcode",
                "url": "https://apply.workable.com/j/NO_SHORTCODE",
            },
            {
                "title": "No URL",
                "shortcode": "NO_URL",
            },
            "not-a-job-dict",
        ],
    }

    def fake_get(
        url: str,
        *,
        timeout: float,
        headers: dict[str, str],
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json=payload,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    jobs = WorkableClient(account_slug="trocaire").fetch_jobs()

    assert len(jobs) == 1
    assert jobs[0]["shortcode"] == "VALID123"


def test_workable_client_rejects_non_object_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(
        url: str,
        *,
        timeout: float,
        headers: dict[str, str],
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json=["not", "an", "object"],
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(
        TypeError,
        match="response must be a JSON object",
    ):
        WorkableClient(account_slug="trocaire").fetch_jobs()


def test_workable_client_rejects_missing_jobs_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(
        url: str,
        *,
        timeout: float,
        headers: dict[str, str],
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={"name": "Trócaire"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(
        TypeError,
        match="must contain a jobs list",
    ):
        WorkableClient(account_slug="trocaire").fetch_jobs()


def test_workable_client_propagates_http_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_get(
        url: str,
        *,
        timeout: float,
        headers: dict[str, str],
    ) -> httpx.Response:
        return httpx.Response(
            404,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(httpx.HTTPStatusError):
        WorkableClient(account_slug="trocaire").fetch_jobs()
