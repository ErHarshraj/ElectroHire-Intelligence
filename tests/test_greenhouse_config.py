import pytest

from packages.common.greenhouse_config import (
    GreenhouseBoardConfig,
    parse_greenhouse_boards,
)


def test_parse_greenhouse_boards() -> None:
    result = parse_greenhouse_boards(
        [
            "Texas Instruments:texas-instruments",
            "Example Electronics:example-electronics",
        ]
    )

    assert result == [
        GreenhouseBoardConfig(
            company_name="Texas Instruments",
            board_token="texas-instruments",
        ),
        GreenhouseBoardConfig(
            company_name="Example Electronics",
            board_token="example-electronics",
        ),
    ]


def test_parse_greenhouse_boards_strips_whitespace() -> None:
    result = parse_greenhouse_boards(
        [
            "  Texas Instruments : texas-instruments  ",
        ]
    )

    assert result == [
        GreenhouseBoardConfig(
            company_name="Texas Instruments",
            board_token="texas-instruments",
        )
    ]


def test_parse_empty_board_list() -> None:
    assert parse_greenhouse_boards([]) == []


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "Texas Instruments",
        "Texas Instruments:",
        ":texas-instruments",
        "Texas Instruments:foo:bar",
    ],
)
def test_parse_greenhouse_boards_rejects_invalid_format(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        parse_greenhouse_boards([value])


def test_parse_greenhouse_boards_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        parse_greenhouse_boards([123])  # type: ignore[list-item]
