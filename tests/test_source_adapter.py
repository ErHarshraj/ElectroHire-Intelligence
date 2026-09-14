from packages.sources import SourceAdapter


class ExampleSourceAdapter(SourceAdapter):
    @property
    def name(self) -> str:
        return "example"

    @property
    def source_type(self) -> str:
        return "job"


def test_source_adapter_contract() -> None:
    source = ExampleSourceAdapter()

    assert source.name == "example"
    assert source.source_type == "job"
