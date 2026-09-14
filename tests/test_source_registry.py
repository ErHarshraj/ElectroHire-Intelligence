import pytest

from packages.source_registry import SourceRegistry
from packages.sources import SourceAdapter, SourceType


class ExampleJobSource(SourceAdapter):
    @property
    def name(self) -> str:
        return "example_job"

    @property
    def source_type(self) -> SourceType:
        return SourceType.JOB


class ExampleStartupSource(SourceAdapter):
    @property
    def name(self) -> str:
        return "example_startup"

    @property
    def source_type(self) -> SourceType:
        return SourceType.STARTUP


def test_register_and_get_source() -> None:
    registry = SourceRegistry()
    source = ExampleJobSource()

    registry.register(source)

    assert registry.get("example_job") is source


def test_duplicate_source_name_is_rejected() -> None:
    registry = SourceRegistry()

    registry.register(ExampleJobSource())

    with pytest.raises(
        ValueError,
        match="Source is already registered",
    ):
        registry.register(ExampleJobSource())


def test_get_missing_source_raises_key_error() -> None:
    registry = SourceRegistry()

    with pytest.raises(KeyError):
        registry.get("missing")


def test_list_returns_sources_in_registration_order() -> None:
    registry = SourceRegistry()

    job_source = ExampleJobSource()
    startup_source = ExampleStartupSource()

    registry.register(job_source)
    registry.register(startup_source)

    assert registry.list() == [job_source, startup_source]


def test_list_can_filter_by_source_type() -> None:
    registry = SourceRegistry()

    job_source = ExampleJobSource()
    startup_source = ExampleStartupSource()

    registry.register(job_source)
    registry.register(startup_source)

    assert registry.list(SourceType.JOB) == [job_source]
    assert registry.list(SourceType.STARTUP) == [startup_source]
    assert registry.list(SourceType.COMPANY) == []
