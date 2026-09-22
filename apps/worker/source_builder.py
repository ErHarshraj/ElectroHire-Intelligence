"""
Build configured job sources for the worker.
"""

from __future__ import annotations

from packages.common.config import Settings
from packages.common.hopin_config import HopinConfig
from packages.job_sources.adzuna.client import AdzunaClient
from packages.job_sources.adzuna.source import AdzunaJobSource
from packages.job_sources.arbeitnow.client import ArbeitnowClient
from packages.job_sources.arbeitnow.source import ArbeitnowJobSource
from packages.job_sources.ayla.client import AylaClient
from packages.job_sources.ayla.source import AylaJobSource
from packages.job_sources.career.ashby import AshbyJobSource
from packages.job_sources.career.greenhouse import GreenhouseJobSource
from packages.job_sources.career.lever import LeverJobSource
from packages.job_sources.career.smartrecruiters import (
    SmartRecruitersJobSource,
)
from packages.job_sources.fourdayweek.client import FourDayWeekClient
from packages.job_sources.fourdayweek.source import FourDayWeekJobSource
from packages.job_sources.himalayas.client import HimalayasClient
from packages.job_sources.himalayas.source import HimalayasJobSource
from packages.job_sources.hopin.client import HopinClient
from packages.job_sources.hopin.source import HopinJobSource
from packages.job_sources.jobicy.client import JobicyClient
from packages.job_sources.jobicy.source import JobicyJobSource
from packages.job_sources.remoteok.client import RemoteOKClient
from packages.job_sources.remoteok.source import RemoteOKJobSource
from packages.job_sources.startup_jobs.client import StartupJobsClient
from packages.job_sources.startup_jobs.source import StartupJobsJobSource
from packages.job_sources.workable.client import WorkableClient
from packages.job_sources.workable.source import WorkableJobSource
from packages.job_sources.workday.client import WorkdayClient
from packages.job_sources.workday.source import WorkdayJobSource
from packages.source_factory import SourceFactoryRegistry
from packages.sources import SourceAdapter, SourceType


def build_job_sources(
    settings: Settings,
    adzuna_client: AdzunaClient | None = None,
) -> list[SourceAdapter]:
    """
    Build all configured job sources.

    Each configured Adzuna query creates an Adzuna source when
    an Adzuna client is available.

    Each configured Greenhouse board creates one Greenhouse source.
    Each configured Lever board creates one Lever source.
    Each configured Ashby board creates one Ashby source.
    Each configured SmartRecruiters board creates one
    SmartRecruiters source.
    Each configured Himalayas source creates one Himalayas source.
    Each configured Jobicy source creates one Jobicy source.
    Each configured Arbeitnow source creates one Arbeitnow source.
    Each configured Remote OK source creates one Remote OK source.
    """
    factory_registry = SourceFactoryRegistry()

    def create_adzuna_source(
        *,
        query: str,
        pages: int,
    ) -> SourceAdapter:
        if adzuna_client is None:
            raise RuntimeError(
                "Adzuna source requested without an Adzuna client."
            )

        return AdzunaJobSource(
            client=adzuna_client,
            query=query,
            pages=pages,
        )

    def create_greenhouse_source(
        *,
        company_name: str,
        board_token: str,
    ) -> SourceAdapter:
        return GreenhouseJobSource(
            company_name=company_name,
            board_token=board_token,
        )

    def create_lever_source(
        *,
        company_name: str,
        site: str,
    ) -> SourceAdapter:
        return LeverJobSource(
            company_name=company_name,
            site=site,
        )

    def create_ashby_source(
        *,
        company_name: str,
        board_name: str,
    ) -> SourceAdapter:
        return AshbyJobSource(
            company_name=company_name,
            board_name=board_name,
        )

    def create_smartrecruiters_source(
        *,
        company_name: str,
        company_identifier: str,
    ) -> SourceAdapter:
        return SmartRecruitersJobSource(
            company_name=company_name,
            company_identifier=company_identifier,
        )

    def create_himalayas_source(
        *,
        limit: int,
    ) -> SourceAdapter:
        return HimalayasJobSource(
            client=HimalayasClient(),
            limit=limit,
        )

    def create_jobicy_source(
        *,
        count: int,
    ) -> SourceAdapter:
        return JobicyJobSource(
            client=JobicyClient(),
            count=count,
        )

    def create_startup_jobs_source(
        *,
        role: str,
    ) -> SourceAdapter:
        return StartupJobsJobSource(
            client=StartupJobsClient(),
            role=role,
        )


    def create_hopin_source(
        *,
        config: HopinConfig,
    ) -> SourceAdapter:
        return HopinJobSource(
            client=HopinClient(),
            config=config,
        )

    def create_fourdayweek_source(
        *,
        limit: int,
    ) -> SourceAdapter:
        return FourDayWeekJobSource(
            client=FourDayWeekClient(),
            limit=limit,
        )


    def create_ayla_source(
        *,
        query: str,
        limit: int,
    ) -> SourceAdapter:
        return AylaJobSource(
            client=AylaClient(),
            query=query,
            limit=limit,
        )


    def create_arbeitnow_source(
        *,
        pages: int,
    ) -> SourceAdapter:
        return ArbeitnowJobSource(
            client=ArbeitnowClient(),
            pages=pages,
        )

    def create_workday_source(
        *,
        tenant: str,
        base_url: str,
        site: str,
        company_name: str,
        batches: int,
    ) -> SourceAdapter:
        return WorkdayJobSource(
            client=WorkdayClient(
                base_url=base_url,
                tenant=tenant,
                site=site,
            ),
            company_name=company_name,
            batches=batches,
        )

    def create_workable_source(
        *,
        account_slug: str,
        company_name: str,
    ) -> SourceAdapter:
        return WorkableJobSource(
            client=WorkableClient(account_slug=account_slug),
            company_name=company_name,
        )


    def create_remoteok_source() -> SourceAdapter:
        return RemoteOKJobSource(client=RemoteOKClient())

    factory_registry.register(
        name="adzuna",
        source_type=SourceType.JOB,
        factory=create_adzuna_source,
    )

    factory_registry.register(
        name="greenhouse",
        source_type=SourceType.JOB,
        factory=create_greenhouse_source,
    )

    factory_registry.register(
        name="lever",
        source_type=SourceType.JOB,
        factory=create_lever_source,
    )

    factory_registry.register(
        name="ashby",
        source_type=SourceType.JOB,
        factory=create_ashby_source,
    )

    factory_registry.register(
        name="smartrecruiters",
        source_type=SourceType.JOB,
        factory=create_smartrecruiters_source,
    )

    factory_registry.register(
        name="himalayas",
        source_type=SourceType.JOB,
        factory=create_himalayas_source,
    )

    factory_registry.register(
        name="jobicy",
        source_type=SourceType.JOB,
        factory=create_jobicy_source,
    )

    factory_registry.register(
        name="startup_jobs",
        source_type=SourceType.JOB,
        factory=create_startup_jobs_source,

    )

    factory_registry.register(
        name="hopin",
        source_type=SourceType.JOB,
        factory=create_hopin_source,
    )

    factory_registry.register(
        name="fourdayweek",
        source_type=SourceType.JOB,
        factory=create_fourdayweek_source,
    )

    factory_registry.register(
        name="ayla",
        source_type=SourceType.JOB,
        factory=create_ayla_source,
    )

    factory_registry.register(
        name="arbeitnow",
        source_type=SourceType.JOB,
        factory=create_arbeitnow_source,
    )

    factory_registry.register(
        name="remoteok",
        source_type=SourceType.JOB,
        factory=create_remoteok_source,
    )

    factory_registry.register(
        name="workday",
        source_type=SourceType.JOB,
        factory=create_workday_source,
    )


    factory_registry.register(
        name="workable",
        source_type=SourceType.JOB,
        factory=create_workable_source,
    )

    sources: list[SourceAdapter] = []

    if adzuna_client is not None:
        adzuna_factory = factory_registry.get("adzuna")

        sources.extend(
            adzuna_factory(
                query=query,
                pages=settings.adzuna_pages,
            )
            for query in settings.adzuna_queries
        )

    greenhouse_factory = factory_registry.get("greenhouse")

    sources.extend(
        greenhouse_factory(
            company_name=board.company_name,
            board_token=board.board_token,
        )
        for board in settings.greenhouse_board_configs
    )

    lever_factory = factory_registry.get("lever")

    sources.extend(
        lever_factory(
            company_name=board.company_name,
            site=board.site,
        )
        for board in settings.lever_board_configs
    )

    ashby_factory = factory_registry.get("ashby")

    sources.extend(
        ashby_factory(
            company_name=board.company_name,
            board_name=board.board_name,
        )
        for board in settings.ashby_board_configs
    )

    smartrecruiters_factory = factory_registry.get(
        "smartrecruiters"
    )

    sources.extend(
        smartrecruiters_factory(
            company_name=board.company_name,
            company_identifier=board.company_identifier,
        )
        for board in settings.smartrecruiters_board_configs
    )

    himalayas_factory = factory_registry.get("himalayas")

    sources.extend(
        himalayas_factory(
            limit=source.limit,
        )
        for source in settings.himalayas_source_configs
    )

    remoteok_factory = factory_registry.get("remoteok")

    sources.extend(
        remoteok_factory()
        for _ in settings.remoteok_source_configs
    )

    jobicy_factory = factory_registry.get("jobicy")

    sources.extend(
        jobicy_factory(
            count=source.count,
        )
        for source in settings.jobicy_source_configs
    )

    startup_jobs_factory = factory_registry.get("startup_jobs")

    sources.extend(
        startup_jobs_factory(
            role=source.role,
        )
        for source in settings.startup_jobs_source_configs
    )

    hopin_factory = factory_registry.get("hopin")

    sources.extend(
        hopin_factory(
            config=source,
        )
        for source in settings.hopin_source_configs
    )

    fourdayweek_factory = factory_registry.get("fourdayweek")

    sources.extend(
        fourdayweek_factory(
            limit=source.limit,
        )
        for source in settings.fourdayweek_source_configs
    )

    ayla_factory = factory_registry.get("ayla")

    sources.extend(
        ayla_factory(
            query=source.query,
            limit=source.limit,
        )
        for source in settings.ayla_source_configs
    )

    arbeitnow_factory = factory_registry.get("arbeitnow")

    sources.extend(
        arbeitnow_factory(
            pages=source.pages,
        )
        for source in settings.arbeitnow_source_configs
    )

    workday_factory = factory_registry.get("workday")

    sources.extend(
        workday_factory(
            tenant=source.tenant,
            base_url=source.base_url,
            site=source.site,
            company_name=source.company_name,
            batches=source.batches,
        )
        for source in settings.workday_source_configs
    )

    workable_factory = factory_registry.get("workable")

    sources.extend(
        workable_factory(
            account_slug=source.account_slug,
            company_name=source.company_name,
        )
        for source in settings.workable_source_configs
    )

    return sources
