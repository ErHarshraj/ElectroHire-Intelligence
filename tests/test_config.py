from packages.common.config import Settings


def test_default_settings() -> None:
    settings = Settings()

    assert settings.app_name == "ElectroHire Intelligence"
    assert settings.app_env == "development"
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 8000
    assert settings.llm_enabled is False
    assert settings.email_enabled is False


