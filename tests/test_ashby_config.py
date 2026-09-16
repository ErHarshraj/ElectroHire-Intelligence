import pytest

from packages.common.ashby_config import parse_ashby_boards


def test_parse_ashby_boards():
    result = parse_ashby_boards(
        ["Ashby:Ashby", "Example Corp:example"]
    )

    assert result[0].company_name == "Ashby"
    assert result[0].board_name == "Ashby"

    assert result[1].company_name == "Example Corp"
    assert result[1].board_name == "example"


def test_parse_ashby_board_rejects_missing_separator():
    with pytest.raises(ValueError, match="Expected format"):
        parse_ashby_boards(["Ashby"])


def test_parse_ashby_board_rejects_empty_company():
    with pytest.raises(
        ValueError,
        match="company name must not be empty",
    ):
        parse_ashby_boards([":Ashby"])


def test_parse_ashby_board_rejects_empty_board():
    with pytest.raises(
        ValueError,
        match="board name must not be empty",
    ):
        parse_ashby_boards(["Ashby:"])


def test_parse_ashby_board_rejects_empty_entry():
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        parse_ashby_boards([""])
