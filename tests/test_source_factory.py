import pytest

from packages.source_factory import SourceFactoryRegistry
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


def create_job_source() -> SourceAdapter:
    return ExampleJobSource()


def create_startup_source() -> SourceAdapter:
    return ExampleStartupSource()


def test_register_and_get_factory() -> None:
    registry = SourceFactoryRegistry()

    registry.register(
        name="example_job",
        source_type=SourceType.JOB,
        factory=create_job_source,
    )

    assert registry.get("example_job") is create_job_source


def test_factory_can_create_source() -> None:
    registry = SourceFactoryRegistry()

    registry.register(
        name="example_job",
        source_type=SourceType.JOB,
        factory=create_job_source,
    )

    source = registry.get("example_job")()

    assert isinstance(source, ExampleJobSource)
    assert source.name == "example_job"
    assert source.source_type == SourceType.JOB


def test_duplicate_factory_name_is_rejected() -> None:
    registry = SourceFactoryRegistry()

    registry.register(
        name="example_job",
        source_type=SourceType.JOB,
        factory=create_job_source,
    )

    with pytest.raises(
        ValueError,
        match="Source factory is already registered",
    ):
        registry.register(
            name="example_job",
            source_type=SourceType.JOB,
            factory=create_job_source,
        )


def test_empty_factory_name_is_rejected() -> None:
    registry = SourceFactoryRegistry()

    with pytest.raises(
        ValueError,
        match="Source factory name must not be empty",
    ):
        registry.register(
            name="   ",
            source_type=SourceType.JOB,
            factory=create_job_source,
        )


def test_missing_factory_raises_key_error() -> None:
    registry = SourceFactoryRegistry()

    with pytest.raises(KeyError):
        registry.get("missing")


def test_source_type_is_available() -> None:
    registry = SourceFactoryRegistry()

    registry.register(
        name="example_job",
        source_type=SourceType.JOB,
        factory=create_job_source,
    )

    assert registry.source_type("example_job") == SourceType.JOB


def test_list_preserves_registration_order() -> None:
    registry = SourceFactoryRegistry()

    registry.register(
        name="example_job",
        source_type=SourceType.JOB,
        factory=create_job_source,
    )
    registry.register(
        name="example_startup",
        source_type=SourceType.STARTUP,
        factory=create_startup_source,
    )

    assert registry.list() == [
        "example_job",
        "example_startup",
    ]


def test_list_can_filter_by_source_type() -> None:
    registry = SourceFactoryRegistry()

    registry.register(
        name="example_job",
        source_type=SourceType.JOB,
        factory=create_job_source,
    )
    registry.register(
        name="example_startup",
        source_type=SourceType.STARTUP,
        factory=create_startup_source,
    )

    assert registry.list(SourceType.JOB) == ["example_job"]
    assert registry.list(SourceType.STARTUP) == ["example_startup"]
    assert registry.list(SourceType.COMPANY) == []
