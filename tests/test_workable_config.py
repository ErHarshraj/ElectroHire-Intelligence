import pytest

from packages.common.workable_config import parse_workable_sources


def test_parse_workable_sources():
    result = parse_workable_sources(
        [
            "trocaire|Trócaire",
            "eurostar|Eurostar International",
        ]
    )

    assert result[0].account_slug == "trocaire"
    assert result[0].company_name == "Trócaire"

    assert result[1].account_slug == "eurostar"
    assert result[1].company_name == "Eurostar International"


def test_parse_workable_source_rejects_missing_separator():
    with pytest.raises(ValueError, match="Expected"):
        parse_workable_sources(["trocaire"])


def test_parse_workable_source_rejects_empty_account_slug():
    with pytest.raises(
        ValueError,
        match="account slug.*must not be empty",
    ):
        parse_workable_sources(["|Trócaire"])


def test_parse_workable_source_rejects_empty_company():
    with pytest.raises(
        ValueError,
        match="company name.*must not be empty",
    ):
        parse_workable_sources(["trocaire|"])


def test_parse_workable_source_skips_empty_entry():
    result = parse_workable_sources(
        [
            "",
            "trocaire|Trócaire",
        ]
    )

    assert len(result) == 1
    assert result[0].account_slug == "trocaire"


def test_parse_workable_sources_skips_whitespace_entries():
    result = parse_workable_sources(
        [
            "   ",
            " eurostar | Eurostar International ",
        ]
    )

    assert len(result) == 1
    assert result[0].account_slug == "eurostar"
    assert result[0].company_name == "Eurostar International"
