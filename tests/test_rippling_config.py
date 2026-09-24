import pytest

from packages.common.rippling_config import parse_rippling_sources


def test_parse_rippling_sources() -> None:
    result = parse_rippling_sources(
        [
            "tylsemi|TYLsemi, Inc.",
            "cbtsindia|CBTS India",
        ]
    )

    assert len(result) == 2

    assert result[0].board_slug == "tylsemi"
    assert result[0].company_name == "TYLsemi, Inc."

    assert result[1].board_slug == "cbtsindia"
    assert result[1].company_name == "CBTS India"


def test_parse_rippling_source_strips_whitespace() -> None:
    result = parse_rippling_sources(
        [
            "  tylsemi | TYLsemi, Inc.  ",
        ]
    )

    assert result[0].board_slug == "tylsemi"
    assert result[0].company_name == "TYLsemi, Inc."


def test_parse_rippling_source_rejects_missing_separator() -> None:
    with pytest.raises(
        ValueError,
        match="Expected: board_slug\\|company_name",
    ):
        parse_rippling_sources(["tylsemi"])


def test_parse_rippling_source_rejects_extra_separator() -> None:
    with pytest.raises(
        ValueError,
        match="Expected: board_slug\\|company_name",
    ):
        parse_rippling_sources(["tylsemi|TYLsemi|extra"])


def test_parse_rippling_source_rejects_empty_board_slug() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        parse_rippling_sources(["|TYLsemi, Inc."])


def test_parse_rippling_source_rejects_empty_company() -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        parse_rippling_sources(["tylsemi|"])


def test_parse_rippling_source_skips_empty_entry() -> None:
    result = parse_rippling_sources(
        [
            "",
            "   ",
            "tylsemi|TYLsemi, Inc.",
        ]
    )

    assert len(result) == 1
    assert result[0].board_slug == "tylsemi"


def test_parse_rippling_sources_empty_list() -> None:
    assert parse_rippling_sources([]) == []
