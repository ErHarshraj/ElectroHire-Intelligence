from datetime import datetime, timezone

from packages.job_sources.startup_jobs.client import StartupJobsClient
from packages.job_sources.startup_jobs.parser import parse_job
from packages.job_sources.startup_jobs.source import StartupJobsJobSource


def test_parse_job_maps_fields() -> None:
    data = {
        "title": "Principal Digital Hardware Engineer (FPGA/VHDL) at Anduril Industries",
        "link": "https://startup.jobs/principal-digital-hardware-engineer-anduril-123456",
        "guid": "https://startup.jobs/principal-digital-hardware-engineer-anduril-10141152",
        "pubDate": "Mon, 21 Sep 2026 00:00:00 +0000",
        "description": (
            "Design digital hardware and FPGA systems.\n\n"
            "California, U.S. · $253,000 – $336,000 per year"
        ),
        "categories": [
            "Engineering",
            "Hardware Engineer",
        ],
    }

    job = parse_job(data)

    assert job.title == "Principal Digital Hardware Engineer (FPGA/VHDL)"
    assert job.company == "Anduril Industries"
    assert job.location == "California, U.S. · $253,000 – $336,000 per year"
    assert job.description == "Design digital hardware and FPGA systems."
    assert job.source == "startup_jobs"
    assert job.source_job_id == "10141152"
    assert (
        str(job.source_url)
        == "https://startup.jobs/principal-digital-hardware-engineer-anduril-10141152"
    )
    assert job.employment_type is None
    assert job.experience_required is None
    assert job.skills == []
    assert job.posted_at == datetime(
        2026,
        9,
        21,
        0,
        0,
        tzinfo=timezone.utc,
    )


def test_parse_job_uses_guid_as_canonical_source_url() -> None:
    data = {
        "title": "Hardware Engineer at Example Robotics",
        "link": "https://startup.jobs/hardware-engineer-example-123?utm_source=rss",
        "guid": "https://startup.jobs/hardware-engineer-example-987654",
    }

    job = parse_job(data)

    assert (
        str(job.source_url)
        == "https://startup.jobs/hardware-engineer-example-987654"
    )


def test_parse_job_extracts_numeric_source_job_id() -> None:
    data = {
        "title": "Embedded Engineer at Example Robotics",
        "guid": "https://startup.jobs/embedded-engineer-example-12345678",
    }

    job = parse_job(data)

    assert job.source_job_id == "12345678"


def test_parse_job_handles_title_without_company_separator() -> None:
    data = {
        "title": "Hardware Engineer",
        "guid": "https://startup.jobs/hardware-engineer-123",
    }

    job = parse_job(data)

    assert job.title == "Hardware Engineer"
    assert job.company == "Unknown"


def test_parse_job_handles_multiple_at_tokens() -> None:
    data = {
        "title": "Senior Engineer at R&D Hardware at Example Robotics",
        "guid": "https://startup.jobs/senior-engineer-123",
    }

    job = parse_job(data)

    assert job.title == "Senior Engineer at R&D Hardware"
    assert job.company == "Example Robotics"


def test_parse_job_handles_single_line_description() -> None:
    data = {
        "title": "Embedded Engineer at Example Robotics",
        "guid": "https://startup.jobs/embedded-engineer-123",
        "description": "Build embedded systems.",
    }

    job = parse_job(data)

    assert job.description == "Build embedded systems."
    assert job.location is None


def test_parse_job_handles_missing_description() -> None:
    data = {
        "title": "Embedded Engineer at Example Robotics",
        "guid": "https://startup.jobs/embedded-engineer-123",
    }

    job = parse_job(data)

    assert job.description is None
    assert job.location is None


def test_parse_job_handles_invalid_timestamp() -> None:
    data = {
        "title": "Embedded Engineer at Example Robotics",
        "guid": "https://startup.jobs/embedded-engineer-123",
        "pubDate": "not-a-timestamp",
    }

    job = parse_job(data)

    assert job.posted_at is None


def test_parse_job_handles_missing_timestamp() -> None:
    data = {
        "title": "Embedded Engineer at Example Robotics",
        "guid": "https://startup.jobs/embedded-engineer-123",
    }

    job = parse_job(data)

    assert job.posted_at is None


def test_parse_job_does_not_map_rss_categories_to_skills() -> None:
    data = {
        "title": "Hardware Engineer at Example Robotics",
        "guid": "https://startup.jobs/hardware-engineer-123",
        "categories": [
            "Engineering",
            "Hardware Engineer",
        ],
    }

    job = parse_job(data)

    assert job.skills == []


def test_parse_job_requires_title() -> None:
    data = {
        "guid": "https://startup.jobs/hardware-engineer-123",
    }

    try:
        parse_job(data)
    except KeyError as exc:
        assert exc.args == ("title",)
    else:
        raise AssertionError("parse_job should require title")


def test_parse_job_requires_guid() -> None:
    data = {
        "title": "Hardware Engineer at Example Robotics",
    }

    try:
        parse_job(data)
    except KeyError as exc:
        assert exc.args == ("guid",)
    else:
        raise AssertionError("parse_job should require guid")


def test_source_fetch_jobs_passes_role_to_client() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.received_role: str | None = None

        def fetch_jobs(
            self,
            *,
            role: str,
        ) -> list[dict[str, object]]:
            self.received_role = role

            return [
                {
                    "title": "Hardware Engineer at Example Robotics",
                    "guid": "https://startup.jobs/hardware-engineer-1",
                },
                {
                    "title": "Embedded Engineer at Example Devices",
                    "guid": "https://startup.jobs/embedded-engineer-2",
                },
            ]

    client = FakeClient()

    source = StartupJobsJobSource(
        client=client,  # type: ignore[arg-type]
        role="hardware-engineer",
    )

    jobs = list(source.fetch_jobs())

    assert client.received_role == "hardware-engineer"
    assert len(jobs) == 2
    assert jobs[0].title == "Hardware Engineer"
    assert jobs[0].company == "Example Robotics"
    assert jobs[1].title == "Embedded Engineer"
    assert jobs[1].source_job_id == "2"


def test_source_identity() -> None:
    class FakeClient:
        def fetch_jobs(
            self,
            *,
            role: str,
        ) -> list[dict[str, object]]:
            return []

    source = StartupJobsJobSource(
        client=FakeClient(),  # type: ignore[arg-type]
        role="hardware-engineer",
    )

    assert source.name == "startup_jobs"
    assert source.source_type.value == "job"


def test_client_fetch_jobs_parses_rss_response(monkeypatch) -> None:
    class FakeResponse:
        content = b"""
        <rss>
            <channel>
                <item>
                    <title>Hardware Engineer at Example Robotics</title>
                    <link>https://startup.jobs/hardware-engineer-123?utm_source=rss</link>
                    <guid>https://startup.jobs/hardware-engineer-123</guid>
                    <pubDate>Mon, 21 Sep 2026 00:00:00 +0000</pubDate>
                    <description>Build hardware systems.

Bengaluru, India</description>
                    <category>Engineering</category>
                    <category>Hardware Engineer</category>
                </item>
                <item>
                    <title>Embedded Engineer at Example Devices</title>
                    <guid>https://startup.jobs/embedded-engineer-456</guid>
                    <description>Build embedded systems.

Remote</description>
                    <category>Engineering</category>
                    <category>Embedded Engineer</category>
                </item>
            </channel>
        </rss>
        """

        def raise_for_status(self) -> None:
            pass

    captured: dict[str, object] = {}

    def fake_get(url, *, params, timeout, headers):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        captured["headers"] = headers
        return FakeResponse()

    monkeypatch.setattr(
        "packages.job_sources.startup_jobs.client.httpx.get",
        fake_get,
    )

    client = StartupJobsClient(timeout=15.0)

    jobs = client.fetch_jobs(role="hardware-engineer")

    assert captured["url"] == StartupJobsClient.BASE_URL
    assert captured["params"] == {"role": "hardware-engineer"}
    assert captured["timeout"] == 15.0

    assert len(jobs) == 2

    assert jobs[0]["title"] == "Hardware Engineer at Example Robotics"
    assert (
        jobs[0]["guid"]
        == "https://startup.jobs/hardware-engineer-123"
    )
    assert jobs[0]["categories"] == [
        "Engineering",
        "Hardware Engineer",
    ]

    assert jobs[1]["title"] == "Embedded Engineer at Example Devices"
    assert jobs[1]["guid"] == "https://startup.jobs/embedded-engineer-456"


def test_client_strips_role_before_request(monkeypatch) -> None:
    class FakeResponse:
        content = b"<rss><channel></channel></rss>"

        def raise_for_status(self) -> None:
            pass

    captured: dict[str, object] = {}

    def fake_get(url, *, params, timeout, headers):
        captured["params"] = params
        return FakeResponse()

    monkeypatch.setattr(
        "packages.job_sources.startup_jobs.client.httpx.get",
        fake_get,
    )

    client = StartupJobsClient()

    jobs = client.fetch_jobs(role="  embedded-engineer  ")

    assert jobs == []
    assert captured["params"] == {"role": "embedded-engineer"}


def test_client_rejects_empty_role() -> None:
    client = StartupJobsClient()

    try:
        client.fetch_jobs(role="   ")
    except ValueError as exc:
        assert str(exc) == "Startup Jobs role must not be empty."
    else:
        raise AssertionError("fetch_jobs should reject an empty role")


def test_client_skips_items_without_title_or_guid(monkeypatch) -> None:
    class FakeResponse:
        content = b"""
        <rss>
            <channel>
                <item>
                    <title>Hardware Engineer at Example Robotics</title>
                    <guid>https://startup.jobs/hardware-engineer-123</guid>
                </item>
                <item>
                    <title>Missing GUID</title>
                </item>
                <item>
                    <guid>https://startup.jobs/missing-title-456</guid>
                </item>
            </channel>
        </rss>
        """

        def raise_for_status(self) -> None:
            pass

    monkeypatch.setattr(
        "packages.job_sources.startup_jobs.client.httpx.get",
        lambda *args, **kwargs: FakeResponse(),
    )

    client = StartupJobsClient()

    jobs = client.fetch_jobs(role="hardware-engineer")

    assert len(jobs) == 1
    assert jobs[0]["title"] == "Hardware Engineer at Example Robotics"


def test_client_raises_for_invalid_xml(monkeypatch) -> None:
    class FakeResponse:
        content = b"<rss><channel><item>invalid"

        def raise_for_status(self) -> None:
            pass

    monkeypatch.setattr(
        "packages.job_sources.startup_jobs.client.httpx.get",
        lambda *args, **kwargs: FakeResponse(),
    )

    client = StartupJobsClient()

    try:
        client.fetch_jobs(role="hardware-engineer")
    except ValueError as exc:
        assert str(exc) == "Startup Jobs RSS response is not valid XML."
    else:
        raise AssertionError("fetch_jobs should reject invalid XML")


def test_client_calls_raise_for_status(monkeypatch) -> None:
    class FakeResponse:
        content = b"<rss><channel></channel></rss>"

        def raise_for_status(self) -> None:
            raise RuntimeError("HTTP failure")

    monkeypatch.setattr(
        "packages.job_sources.startup_jobs.client.httpx.get",
        lambda *args, **kwargs: FakeResponse(),
    )

    client = StartupJobsClient()

    try:
        client.fetch_jobs(role="hardware-engineer")
    except RuntimeError as exc:
        assert str(exc) == "HTTP failure"
    else:
        raise AssertionError("fetch_jobs should propagate HTTP errors")
