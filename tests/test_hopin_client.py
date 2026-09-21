import httpx

from packages.job_sources.hopin.client import HopinClient


def test_fetch_jobs_sends_supported_filters(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, object]:
            return {
                "jobs": [
                    {
                        "id": "job-1",
                        "company": "Example Electronics",
                        "title": "Embedded Engineer",
                    }
                ]
            }

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        captured["url"] = url
        captured["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr(httpx, "get", fake_get)

    jobs = HopinClient().fetch_jobs(
        industry="Technology",
        location="Bangalore, India",
        work_type="Remote",
        role_type="Embedded Engineer",
        unofficial=False,
    )

    assert len(jobs) == 1
    assert jobs[0]["id"] == "job-1"
    assert captured["url"] == "https://api.hopinjobs.com/api/jobs"

    kwargs = captured["kwargs"]
    assert isinstance(kwargs, dict)

    assert kwargs["params"] == {
        "is_unofficial": "false",
        "industry": "Technology",
        "location": "Bangalore, India",
        "work_type": "Remote",
        "role_type": "Embedded Engineer",
    }


def test_fetch_internships_uses_internship_endpoint(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, object]:
            return {
                "internships": [
                    {
                        "id": "internship-1",
                        "company": "Example Electronics",
                        "title": "Embedded Intern",
                    }
                ]
            }

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        captured["url"] = url
        return FakeResponse()

    monkeypatch.setattr(httpx, "get", fake_get)

    internships = HopinClient().fetch_internships(
        industry="Technology",
    )

    assert len(internships) == 1
    assert internships[0]["title"] == "Embedded Intern"
    assert captured["url"] == (
        "https://api.hopinjobs.com/api/internships"
    )


def test_unofficial_defaults_to_false(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, object]:
            return {"jobs": []}

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        captured["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr(httpx, "get", fake_get)

    HopinClient().fetch_jobs()

    kwargs = captured["kwargs"]
    assert isinstance(kwargs, dict)
    assert kwargs["params"] == {
        "is_unofficial": "false",
    }


def test_fetch_jobs_rejects_invalid_response_shape(monkeypatch) -> None:
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

    try:
        HopinClient().fetch_jobs()
    except TypeError as exc:
        assert "JSON object" in str(exc)
    else:
        raise AssertionError("Expected TypeError")


def test_fetch_jobs_rejects_missing_jobs_list(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, object]:
            return {}

    monkeypatch.setattr(
        httpx,
        "get",
        lambda url, **kwargs: FakeResponse(),
    )

    try:
        HopinClient().fetch_jobs()
    except TypeError as exc:
        assert "jobs list" in str(exc)
    else:
        raise AssertionError("Expected TypeError")


def test_fetch_jobs_filters_invalid_records(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, object]:
            return {
                "jobs": [
                    {
                        "id": "valid",
                        "company": "Example",
                        "title": "Engineer",
                    },
                    {
                        "id": "missing-company",
                        "title": "Engineer",
                    },
                    {
                        "id": "missing-title",
                        "company": "Example",
                    },
                    "invalid-record",
                ]
            }

    monkeypatch.setattr(
        httpx,
        "get",
        lambda url, **kwargs: FakeResponse(),
    )

    jobs = HopinClient().fetch_jobs()

    assert jobs == [
        {
            "id": "valid",
            "company": "Example",
            "title": "Engineer",
        }
    ]
