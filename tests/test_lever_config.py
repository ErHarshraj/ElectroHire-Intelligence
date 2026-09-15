import pytest

from packages.common.lever_config import (
    LeverBoardConfig,
    parse_lever_boards,
)


def test_parse_lever_boards() -> None:
    boards = parse_lever_boards(
        [
            "Palantir:palantir",
            "Example Electronics:example-electronics",
        ]
    )

    assert boards == [
        LeverBoardConfig(
            company_name="Palantir",
            site="palantir",
        ),
        LeverBoardConfig(
            company_name="Example Electronics",
            site="example-electronics",
        ),
    ]


def test_parse_lever_boards_strips_whitespace() -> None:
    boards = parse_lever_boards(
        [
            "  Palantir : palantir  ",
        ]
    )

    assert boards == [
        LeverBoardConfig(
            company_name="Palantir",
            site="palantir",
        )
    ]


def test_parse_lever_boards_empty_list() -> None:
    assert parse_lever_boards([]) == []


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "Palantir",
        ":palantir",
        "Palantir:",
        "Palantir:one:two",
    ],
)
def test_parse_lever_boards_rejects_invalid_values(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        parse_lever_boards([value])


def test_parse_lever_boards_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        parse_lever_boards([123])  # type: ignore[list-item]
