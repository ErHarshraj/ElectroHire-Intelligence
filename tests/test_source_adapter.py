from packages.sources import SourceAdapter, SourceType


class ExampleSourceAdapter(SourceAdapter):
    @property
    def name(self) -> str:
        return "example"

    @property
    def source_type(self) -> SourceType:
        return SourceType.JOB


def test_source_adapter_contract() -> None:
    source = ExampleSourceAdapter()

    assert source.name == "example"
    assert source.source_type == SourceType.JOB
    assert source.source_type.value == "job"


def test_source_type_values() -> None:
    assert SourceType.JOB.value == "job"
    assert SourceType.STARTUP.value == "startup"
    assert SourceType.COMPANY.value == "company"
