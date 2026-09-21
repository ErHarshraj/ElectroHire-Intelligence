from unittest.mock import Mock

from apps.worker.source_builder import build_job_sources
from packages.common.config import Settings
from packages.job_sources.adzuna.source import AdzunaJobSource
from packages.job_sources.arbeitnow.source import ArbeitnowJobSource
from packages.job_sources.career.greenhouse import GreenhouseJobSource
from packages.job_sources.career.lever import LeverJobSource
from packages.job_sources.himalayas.source import HimalayasJobSource
from packages.job_sources.jobicy.source import JobicyJobSource
from packages.job_sources.remoteok.source import RemoteOKJobSource
from packages.job_sources.workday.source import WorkdayJobSource


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


def test_build_job_sources_creates_greenhouse_without_adzuna_client() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[],
        greenhouse_boards=[
            "Texas Instruments:texas-instruments",
        ],
    )

    sources = build_job_sources(settings=settings)

    assert len(sources) == 1
    assert isinstance(sources[0], GreenhouseJobSource)


def test_build_job_sources_creates_lever_without_adzuna_client() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[],
        lever_boards=[
            "Palantir:palantir",
        ],
    )

    sources = build_job_sources(settings=settings)

    assert len(sources) == 1
    assert isinstance(sources[0], LeverJobSource)


def test_build_job_sources_skips_adzuna_without_client() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[
            "embedded hardware",
        ],
        greenhouse_boards=[
            "Texas Instruments:texas-instruments",
        ],
    )

    sources = build_job_sources(settings=settings)

    assert len(sources) == 1
    assert isinstance(sources[0], GreenhouseJobSource)


def test_build_job_sources_creates_smartrecruiters_without_adzuna_client():
    settings = Settings(
        adzuna_app_id=None,
        adzuna_app_key=None,
        smartrecruiters_boards=[
            "Example Corp:examplecorp"
        ],
        himalayas_sources=[],
        remoteok_sources=[],
    )

    sources = build_job_sources(
        settings=settings,
        adzuna_client=None,
    )

    assert len(sources) == 1
    assert sources[0].name == "smartrecruiters:examplecorp"


def test_build_job_sources_skips_smartrecruiters_when_not_configured():
    settings = Settings(
        adzuna_app_id=None,
        adzuna_app_key=None,
        smartrecruiters_boards=[],
        himalayas_sources=[],
        remoteok_sources=[],
    )

    sources = build_job_sources(
        settings=settings,
        adzuna_client=None,
    )

    assert sources == []


def test_build_job_sources_creates_himalayas_sources() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[],
        himalayas_sources=[
            "himalayas:25",
            "himalayas-large:100",
        ],
    )

    sources = build_job_sources(settings=settings)

    assert len(sources) == 2
    assert all(
        isinstance(source, HimalayasJobSource)
        for source in sources
    )

    assert sources[0].name == "himalayas"
    assert sources[0].limit == 25

    assert sources[1].name == "himalayas"
    assert sources[1].limit == 100


def test_build_job_sources_creates_remoteok_sources() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[],
        greenhouse_boards=[],
        lever_boards=[],
        ashby_boards=[],
        smartrecruiters_boards=[],
        himalayas_sources=[],
        remoteok_sources=["remoteok"],
    )

    sources = build_job_sources(settings=settings)

    assert len(sources) == 1
    assert isinstance(sources[0], RemoteOKJobSource)
    assert sources[0].name == "remoteok"


def test_build_job_sources_creates_jobicy_sources() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[],
        greenhouse_boards=[],
        lever_boards=[],
        ashby_boards=[],
        smartrecruiters_boards=[],
        himalayas_sources=[],
        remoteok_sources=[],
        jobicy_sources=[
            "jobicy:50",
            "jobicy-large:100",
        ],
    )

    sources = build_job_sources(settings=settings)

    assert len(sources) == 2
    assert all(
        isinstance(source, JobicyJobSource)
        for source in sources
    )

    assert sources[0].name == "jobicy"
    assert sources[0].count == 50

    assert sources[1].name == "jobicy"
    assert sources[1].count == 100


def test_build_job_sources_creates_arbeitnow_sources() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[],
        arbeitnow_sources=["arbeitnow:2"],
    )

    sources = build_job_sources(settings=settings)

    assert len(sources) == 1
    assert isinstance(sources[0], ArbeitnowJobSource)
    assert sources[0].pages == 2


def test_build_job_sources_creates_multiple_arbeitnow_sources() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[],
        arbeitnow_sources=[
            "arbeitnow:1",
            "arbeitnow:3",
        ],
    )

    sources = build_job_sources(settings=settings)

    assert len(sources) == 2
    assert all(
        isinstance(source, ArbeitnowJobSource)
        for source in sources
    )
    assert sources[0].pages == 1
    assert sources[1].pages == 3


def test_build_job_sources_has_no_arbeitnow_sources_when_unconfigured() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[],
        arbeitnow_sources=[],
    )

    sources = build_job_sources(settings=settings)

    assert not any(
        isinstance(source, ArbeitnowJobSource)
        for source in sources
    )


def test_build_job_sources_creates_workday_sources() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[],
        workday_sources=[
            "analogdevices|https://analogdevices.wd1.myworkdayjobs.com"
            "|External|Analog Devices|3",
        ],
    )

    sources = build_job_sources(settings=settings)

    assert len(sources) == 1
    assert isinstance(sources[0], WorkdayJobSource)
    assert sources[0].name == "workday"
    assert sources[0].company_name == "Analog Devices"
    assert sources[0].batches == 3

    assert sources[0].client.tenant == "analogdevices"
    assert (
        sources[0].client.base_url
        == "https://analogdevices.wd1.myworkdayjobs.com"
    )
    assert sources[0].client.site == "External"


def test_build_job_sources_creates_multiple_workday_sources() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[],
        workday_sources=[
            "analogdevices|https://analogdevices.wd1.myworkdayjobs.com"
            "|External|Analog Devices|3",
            "ti|https://ti.wd1.myworkdayjobs.com"
            "|External|Texas Instruments|5",
        ],
    )

    sources = build_job_sources(settings=settings)

    assert len(sources) == 2
    assert all(
        isinstance(source, WorkdayJobSource)
        for source in sources
    )

    assert sources[0].company_name == "Analog Devices"
    assert sources[0].batches == 3
    assert sources[0].client.tenant == "analogdevices"

    assert sources[1].company_name == "Texas Instruments"
    assert sources[1].batches == 5
    assert sources[1].client.tenant == "ti"


def test_build_job_sources_has_no_workday_sources_when_unconfigured() -> None:
    settings = Settings(
        _env_file=None,
        adzuna_queries=[],
        workday_sources=[],
    )

    sources = build_job_sources(settings=settings)

    assert sources == []
