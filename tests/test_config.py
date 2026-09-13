from packages.application.models import ApplicationExecutionMode
from packages.common.config import Settings


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
