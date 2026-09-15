"""
Build configured job sources for the worker.
"""

from __future__ import annotations

from packages.common.config import Settings
from packages.job_sources.adzuna.client import AdzunaClient
from packages.job_sources.adzuna.source import AdzunaJobSource
from packages.job_sources.career.greenhouse import GreenhouseJobSource
from packages.job_sources.career.lever import LeverJobSource
from packages.source_factory import SourceFactoryRegistry
from packages.sources import SourceAdapter, SourceType


def build_job_sources(
    settings: Settings,
    adzuna_client: AdzunaClient,
) -> list[SourceAdapter]:
    """
    Build all configured job sources.

    Each configured Adzuna query creates one Adzuna source.
    Each configured Greenhouse board creates one Greenhouse source.
    Each configured Lever board creates one Lever source.
    """

    factory_registry = SourceFactoryRegistry()

    def create_adzuna_source(
        *,
        query: str,
        pages: int,
    ) -> SourceAdapter:
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

    sources: list[SourceAdapter] = []

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

    return sources
