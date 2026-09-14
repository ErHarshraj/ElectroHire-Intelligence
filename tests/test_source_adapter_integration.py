from packages.job_sources.adzuna.source import AdzunaJobSource
from packages.opportunity.sources.google_news import GoogleNewsStartupSource
from packages.sources import SourceAdapter, SourceType


def test_adzuna_source_implements_common_source_adapter() -> None:
    assert issubclass(AdzunaJobSource, SourceAdapter)

    source = object.__new__(AdzunaJobSource)

    assert source.name == "adzuna"
    assert source.source_type == SourceType.JOB


def test_google_news_source_implements_common_source_adapter() -> None:
    assert issubclass(GoogleNewsStartupSource, SourceAdapter)

    source = GoogleNewsStartupSource()

    assert source.name == "google_news"
    assert source.source_type == SourceType.STARTUP
