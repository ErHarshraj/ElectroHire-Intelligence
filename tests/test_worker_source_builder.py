from unittest.mock import Mock

from apps.worker.source_builder import build_job_sources
from packages.common.config import Settings
from packages.job_sources.adzuna.source import AdzunaJobSource
from packages.job_sources.career.greenhouse import GreenhouseJobSource
from packages.job_sources.career.lever import LeverJobSource


def test_build_job_sources_creates_adzuna_sources() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[
            "embedded hardware",
            "pcb design",
        ],
        adzuna_pages=2,
    )

    client = Mock()

    sources = build_job_sources(
        settings=settings,
        adzuna_client=client,
    )

    assert len(sources) == 2
    assert all(isinstance(source, AdzunaJobSource) for source in sources)

    assert sources[0].query == "embedded hardware"
    assert sources[0].pages == 2

    assert sources[1].query == "pcb design"
    assert sources[1].pages == 2


def test_build_job_sources_creates_greenhouse_sources() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[],
        greenhouse_boards=[
            "Texas Instruments:texas-instruments",
            "Example Electronics:example-electronics",
        ],
    )

    client = Mock()

    sources = build_job_sources(
        settings=settings,
        adzuna_client=client,
    )

    assert len(sources) == 2
    assert all(
        isinstance(source, GreenhouseJobSource)
        for source in sources
    )

    assert sources[0].company_name == "Texas Instruments"
    assert sources[0].board_token == "texas-instruments"

    assert sources[1].company_name == "Example Electronics"
    assert sources[1].board_token == "example-electronics"


def test_build_job_sources_supports_adzuna_and_greenhouse_together() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=["embedded hardware"],
        greenhouse_boards=[
            "Texas Instruments:texas-instruments",
        ],
    )

    client = Mock()

    sources = build_job_sources(
        settings=settings,
        adzuna_client=client,
    )

    assert len(sources) == 2
    assert isinstance(sources[0], AdzunaJobSource)
    assert isinstance(sources[1], GreenhouseJobSource)


def test_build_job_sources_has_no_greenhouse_sources_when_unconfigured() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=["embedded hardware"],
        greenhouse_boards=[],
    )

    client = Mock()

    sources = build_job_sources(
        settings=settings,
        adzuna_client=client,
    )

    assert len(sources) == 1
    assert isinstance(sources[0], AdzunaJobSource)


def test_build_job_sources_creates_lever_sources() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[],
        lever_boards=[
            "Palantir:palantir",
            "Example Electronics:example-electronics",
        ],
    )

    client = Mock()

    sources = build_job_sources(
        settings=settings,
        adzuna_client=client,
    )

    assert len(sources) == 2
    assert all(
        isinstance(source, LeverJobSource)
        for source in sources
    )

    assert sources[0].company_name == "Palantir"
    assert sources[0].site == "palantir"

    assert sources[1].company_name == "Example Electronics"
    assert sources[1].site == "example-electronics"


def test_build_job_sources_supports_all_configured_sources() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=["embedded hardware"],
        greenhouse_boards=[
            "Texas Instruments:texas-instruments",
        ],
        lever_boards=[
            "Palantir:palantir",
        ],
    )

    client = Mock()

    sources = build_job_sources(
        settings=settings,
        adzuna_client=client,
    )

    assert len(sources) == 3
    assert isinstance(sources[0], AdzunaJobSource)
    assert isinstance(sources[1], GreenhouseJobSource)
    assert isinstance(sources[2], LeverJobSource)


def test_build_job_sources_has_no_lever_sources_when_unconfigured() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=["embedded hardware"],
        lever_boards=[],
    )

    client = Mock()

    sources = build_job_sources(
        settings=settings,
        adzuna_client=client,
    )

    assert len(sources) == 1
    assert isinstance(sources[0], AdzunaJobSource)
