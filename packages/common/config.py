from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from packages.application.models import ApplicationExecutionMode
from packages.common.ashby_config import (
    AshbyBoardConfig,
    parse_ashby_boards,
)
from packages.common.greenhouse_config import (
    GreenhouseBoardConfig,
    parse_greenhouse_boards,
)
from packages.common.lever_config import (
    LeverBoardConfig,
    parse_lever_boards,
)


class Settings(BaseSettings):
    app_name: str = "ElectroHire Intelligence"
    app_env: str = "development"
    app_debug: bool = False

    api_host: str = "127.0.0.1"
    api_port: int = 8000

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "electrohire"
    postgres_user: str = "electrohire"
    postgres_password: str = "CHANGE_ME"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    secret_key: str = "CHANGE_ME"

    adzuna_app_id: str | None = None
    adzuna_app_key: str | None = None
    adzuna_country: str = "in"
    adzuna_queries: list[str] = [
        "embedded hardware",
        "hardware design engineer",
        "embedded systems engineer",
        "PCB design engineer",
        "electronics engineer",
        "firmware engineer",
        "robotics hardware engineer",
    ]
    adzuna_pages: int = 1

    greenhouse_boards: list[str] = []

    @property
    def greenhouse_board_configs(self) -> list[GreenhouseBoardConfig]:
        """Return parsed Greenhouse career-board configurations."""
        return parse_greenhouse_boards(self.greenhouse_boards)

    lever_boards: list[str] = []

    @property
    def lever_board_configs(self) -> list[LeverBoardConfig]:
        """Return parsed Lever career-board configurations."""
        return parse_lever_boards(self.lever_boards)

    ashby_boards: list[str] = []

    @property
    def ashby_board_configs(self) -> list[AshbyBoardConfig]:
        """Return parsed Ashby career-board configurations."""
        return parse_ashby_boards(self.ashby_boards)


    scheduler_discovery_interval_minutes: int = 60
    scheduler_recovery_interval_minutes: int = 30
    llm_enabled: bool = False
    llm_api_key: str | None = None

    email_enabled: bool = False
    browser_enabled: bool = False
    application_execution_mode: ApplicationExecutionMode = ApplicationExecutionMode.DRY_RUN
    browser_headless: bool = True
    browser_timeout_ms: int = 15000
    browser_executable_path: str | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None

    candidate_name: str = "Harshraj"
    candidate_email: str | None = None
    candidate_phone: str | None = None
    candidate_location: str | None = None
    candidate_resume_path: str | None = None
    candidate_linkedin_url: str | None = None
    candidate_github_url: str | None = None
    candidate_portfolio_url: str | None = None

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
