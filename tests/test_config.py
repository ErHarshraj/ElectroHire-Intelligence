from packages.application.models import ApplicationExecutionMode
from packages.common.config import Settings
from packages.common.greenhouse_config import GreenhouseBoardConfig
from packages.common.lever_config import LeverBoardConfig


def test_default_settings() -> None:
    settings = Settings(_env_file=None, api_port=8000)

    assert settings.app_name == "ElectroHire Intelligence"
    assert settings.app_env == "development"
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 8000
    assert settings.llm_enabled is False
    assert settings.email_enabled is False


def test_default_application_execution_mode_is_dry_run() -> None:
    settings = Settings(_env_file=None, api_port=8000)

    assert settings.application_execution_mode == ApplicationExecutionMode.DRY_RUN


def test_application_execution_mode_reads_from_environment() -> None:
    settings = Settings(
        _env_file=None,
        application_execution_mode="full_auto",
    )

    assert settings.application_execution_mode == ApplicationExecutionMode.FULL_AUTO


def test_greenhouse_boards_default_to_empty_list() -> None:
    settings = Settings(_env_file=None)

    assert settings.greenhouse_boards == []


def test_greenhouse_boards_read_from_environment() -> None:
    settings = Settings(
        _env_file=None,
        greenhouse_boards=[
            "Example Electronics:example-token",
            "Another Company:another-token",
        ],
    )

    assert settings.greenhouse_boards == [
        "Example Electronics:example-token",
        "Another Company:another-token",
    ]


def test_greenhouse_boards_read_from_environment_variable(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "GREENHOUSE_BOARDS",
        '["Texas Instruments:texas-instruments",'
        '"Example Electronics:example-electronics"]',
    )

    settings = Settings(_env_file=None)

    assert settings.greenhouse_boards == [
        "Texas Instruments:texas-instruments",
        "Example Electronics:example-electronics",
    ]


def test_greenhouse_board_configs_are_parsed() -> None:
    settings = Settings(
        _env_file=None,
        greenhouse_boards=[
            "Texas Instruments:texas-instruments",
            "Example Electronics:example-electronics",
        ],
    )

    assert settings.greenhouse_board_configs == [
        GreenhouseBoardConfig(
            company_name="Texas Instruments",
            board_token="texas-instruments",
        ),
        GreenhouseBoardConfig(
            company_name="Example Electronics",
            board_token="example-electronics",
        ),
    ]


def test_greenhouse_board_configs_are_empty_when_not_configured() -> None:
    settings = Settings(_env_file=None)

    assert settings.greenhouse_board_configs == []


def test_lever_board_configs_are_parsed() -> None:
    settings = Settings(
        _env_file=None,
        lever_boards=[
            "Palantir:palantir",
            "Example Electronics:example-electronics",
        ],
    )

    assert settings.lever_board_configs == [
        LeverBoardConfig(
            company_name="Palantir",
            site="palantir",
        ),
        LeverBoardConfig(
            company_name="Example Electronics",
            site="example-electronics",
        ),
    ]


def test_lever_board_configs_are_empty_when_not_configured() -> None:
    settings = Settings(_env_file=None)

    assert settings.lever_board_configs == []
