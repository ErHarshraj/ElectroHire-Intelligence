from apps.worker.source_builder import build_job_sources
from packages.common.config import Settings
from packages.job_sources.adzuna.client import AdzunaClient
from packages.job_sources.adzuna.source import AdzunaJobSource
from packages.job_sources.career.greenhouse import GreenhouseJobSource


def test_build_job_sources_creates_adzuna_sources() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=["hardware engineer", "embedded engineer"],
        adzuna_pages=2,
    )

    client = AdzunaClient(
        app_id="test-app-id",
        app_key="test-app-key",
    )

    sources = build_job_sources(
        settings=settings,
        adzuna_client=client,
    )

    adzuna_sources = [
        source
        for source in sources
        if isinstance(source, AdzunaJobSource)
    ]

    assert len(adzuna_sources) == 2
    assert adzuna_sources[0].query == "hardware engineer"
    assert adzuna_sources[1].query == "embedded engineer"
    assert all(source.pages == 2 for source in adzuna_sources)


def test_build_job_sources_creates_greenhouse_sources() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[],
        greenhouse_boards=[
            "Texas Instruments:texas-instruments",
            "Example Electronics:example-electronics",
        ],
    )

    client = AdzunaClient(
        app_id="test-app-id",
        app_key="test-app-key",
    )

    sources = build_job_sources(
        settings=settings,
        adzuna_client=client,
    )

    greenhouse_sources = [
        source
        for source in sources
        if isinstance(source, GreenhouseJobSource)
    ]

    assert len(greenhouse_sources) == 2

    assert greenhouse_sources[0].company_name == "Texas Instruments"
    assert greenhouse_sources[0].board_token == "texas-instruments"

    assert greenhouse_sources[1].company_name == "Example Electronics"
    assert greenhouse_sources[1].board_token == "example-electronics"


def test_build_job_sources_supports_adzuna_and_greenhouse_together() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=["hardware engineer"],
        adzuna_pages=1,
        greenhouse_boards=[
            "Texas Instruments:texas-instruments",
        ],
    )

    client = AdzunaClient(
        app_id="test-app-id",
        app_key="test-app-key",
    )

    sources = build_job_sources(
        settings=settings,
        adzuna_client=client,
    )

    assert len(sources) == 2
    assert isinstance(sources[0], AdzunaJobSource)
    assert isinstance(sources[1], GreenhouseJobSource)


def test_build_job_sources_uses_no_greenhouse_sources_when_unconfigured() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=["hardware engineer"],
    )

    client = AdzunaClient(
        app_id="test-app-id",
        app_key="test-app-key",
    )

    sources = build_job_sources(
        settings=settings,
        adzuna_client=client,
    )

    assert len(sources) == 1
    assert isinstance(sources[0], AdzunaJobSource)
