
import httpx
from pytest import MonkeyPatch

from packages.job_sources.adzuna.client import AdzunaClient
from packages.job_sources.adzuna.parser import parse_job


def test_parse_job() -> None:
    data = {
        "id": "123456",
        "title": "Embedded Hardware Engineer",
        "description": "Design embedded hardware systems.",
        "redirect_url": "https://example.com/jobs/123456",
        "created": "2026-08-29T10:30:00Z",
        "company": {
            "display_name": "Example Electronics",
        },
        "location": {
            "display_name": "Bengaluru",
        },
    }

    job = parse_job(data)

    assert job.title == "Embedded Hardware Engineer"
    assert job.company == "Example Electronics"
    assert job.location == "Bengaluru"
    assert job.source == "adzuna"
    assert job.source_job_id == "123456"
    assert str(job.source_url) == "https://example.com/jobs/123456"
    assert job.description == "Design embedded hardware systems."
    assert job.posted_at is not None


def test_adzuna_client_search_jobs(
    monkeypatch: MonkeyPatch,
) -> None:
    expected: dict[str, object] = {
        "results": [
            {
                "id": "123",
                "title": "Embedded Engineer",
            }
        ]
    }

    def mock_get(
        url: str,
        *,
        params: dict[str, str | int],
        timeout: float,
    ) -> httpx.Response:
        assert url == (
            "https://api.adzuna.com/v1/api/"
            "jobs/in/search/1"
        )
        assert params["app_id"] == "test-app-id"
        assert params["app_key"] == "test-app-key"
        assert params["what"] == "embedded"
        assert params["results_per_page"] == 20
        assert timeout == 10.0

        return httpx.Response(
            200,
            json=expected,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", mock_get)

    client = AdzunaClient(
        app_id="test-app-id",
        app_key="test-app-key",
    )

    result = client.search_jobs("embedded")

    assert result == expected


def test_adzuna_client_raises_for_http_error(
    monkeypatch: MonkeyPatch,
) -> None:
    def mock_get(
        url: str,
        *,
        params: dict[str, str | int],
        timeout: float,
    ) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": "Unauthorized"},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", mock_get)

    client = AdzunaClient(
        app_id="bad-id",
        app_key="bad-key",
    )

    try:
        client.search_jobs("embedded")
    except httpx.HTTPStatusError as exc:
        assert exc.response.status_code == 401
    else:
        raise AssertionError("Expected HTTPStatusError")


def test_adzuna_job_source_fetches_and_parses_jobs(
    monkeypatch: MonkeyPatch,
) -> None:
    expected: dict[str, object] = {
        "results": [
            {
                "id": "123",
                "title": "Embedded Hardware Engineer",
                "description": "Design embedded hardware systems.",
                "redirect_url": "https://example.com/jobs/123",
                "created": "2026-08-29T10:30:00Z",
                "company": {
                    "display_name": "Example Electronics",
                },
                "location": {
                    "display_name": "Bengaluru",
                },
            }
        ]
    }

    def mock_search_jobs(
        self: AdzunaClient,
        query: str,
        page: int = 1,
        results_per_page: int = 20,
    ) -> dict[str, object]:
        assert query == "embedded hardware"
        return expected

    monkeypatch.setattr(
        AdzunaClient,
        "search_jobs",
        mock_search_jobs,
    )

    from packages.job_sources.adzuna.source import AdzunaJobSource

    client = AdzunaClient(
        app_id="test-app-id",
        app_key="test-app-key",
    )

    source = AdzunaJobSource(
        client=client,
        query="embedded hardware",
    )

    jobs = list(source.fetch_jobs())

    assert len(jobs) == 1
    assert jobs[0].title == "Embedded Hardware Engineer"
    assert jobs[0].company == "Example Electronics"
    assert jobs[0].source == "adzuna"
    assert jobs[0].source_job_id == "123"

def test_parse_job_handles_missing_company_name() -> None:
    data = {
        "id": "999",
        "title": "Embedded Hardware Engineer",
        "description": "Hardware engineering role.",
        "redirect_url": "https://example.com/jobs/999",
        "created": "2026-08-29T10:30:00Z",
        "company": {
            "__CLASS__": "Adzuna::API::Response::Company",
        },
        "location": {
            "display_name": "Bangalore, Karnataka",
        },
    }

    job = parse_job(data)

    assert job.title == "Embedded Hardware Engineer"
    assert job.company == "Unknown"
    assert job.location == "Bangalore, Karnataka"
