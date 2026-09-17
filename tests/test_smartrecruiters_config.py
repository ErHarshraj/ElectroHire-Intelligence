import pytest

from packages.common.smartrecruiters_config import (
    parse_smartrecruiters_boards,
)


def test_parse_smartrecruiters_boards():
    result = parse_smartrecruiters_boards(
        [
            "SmartRecruiters:smartrecruiters",
            "Example Corp:examplecorp",
        ]
    )

    assert result[0].company_name == "SmartRecruiters"
    assert result[0].company_identifier == "smartrecruiters"

    assert result[1].company_name == "Example Corp"
    assert result[1].company_identifier == "examplecorp"


def test_parse_smartrecruiters_board_rejects_missing_separator():
    with pytest.raises(ValueError, match="Expected format"):
        parse_smartrecruiters_boards(["SmartRecruiters"])


def test_parse_smartrecruiters_board_rejects_empty_company():
    with pytest.raises(
        ValueError,
        match="company name must not be empty",
    ):
        parse_smartrecruiters_boards([":smartrecruiters"])


def test_parse_smartrecruiters_board_rejects_empty_identifier():
    with pytest.raises(
        ValueError,
        match="company identifier must not be empty",
    ):
        parse_smartrecruiters_boards(["SmartRecruiters:"])


def test_parse_smartrecruiters_board_rejects_empty_entry():
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        parse_smartrecruiters_boards([""])
