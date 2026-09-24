from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from packages.application.models import ApplicationExecutionMode
from packages.common.arbeitnow_config import (
    ArbeitnowConfig,
    parse_arbeitnow_sources,
)
from packages.common.ashby_config import (
    AshbyBoardConfig,
    parse_ashby_boards,
)
from packages.common.ayla_config import (
    AylaConfig,
    parse_ayla_sources,
)
from packages.common.fourdayweek_config import (
    FourDayWeekConfig,
    parse_fourdayweek_sources,
)
from packages.common.greenhouse_config import (
    GreenhouseBoardConfig,
    parse_greenhouse_boards,
)
from packages.common.himalayas_config import (
    HimalayasConfig,
    parse_himalayas_sources,
)
from packages.common.hopin_config import (
    HopinConfig,
    parse_hopin_sources,
)
from packages.common.jobicy_config import (
    JobicyConfig,
    parse_jobicy_sources,
)
from packages.common.lever_config import (
    LeverBoardConfig,
    parse_lever_boards,
)
from packages.common.remoteok_config import (
    RemoteOKConfig,
    parse_remoteok_sources,
)
from packages.common.rippling_config import (
    RipplingConfig,
    parse_rippling_sources,
)
from packages.common.smartrecruiters_config import (
    SmartRecruitersBoardConfig,
    parse_smartrecruiters_boards,
)
from packages.common.startup_jobs_config import (
    StartupJobsConfig,
    parse_startup_jobs_sources,
)
from packages.common.workable_config import (
    WorkableConfig,
    parse_workable_sources,
)
from packages.common.workday_config import (
    WorkdayConfig,
    parse_workday_sources,
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

    smartrecruiters_boards: list[str] = []

    @property
    def smartrecruiters_board_configs(
        self,
    ) -> list[SmartRecruitersBoardConfig]:
        """Return parsed SmartRecruiters career-board configurations."""
        return parse_smartrecruiters_boards(self.smartrecruiters_boards)

    himalayas_sources: list[str] = []

    @property
    def himalayas_source_configs(self) -> list[HimalayasConfig]:
        """Return parsed Himalayas source configurations."""
        return parse_himalayas_sources(self.himalayas_sources)

    remoteok_sources: list[str] = []

    @property
    def remoteok_source_configs(self) -> list[RemoteOKConfig]:
        """Return parsed Remote OK source configurations."""
        return parse_remoteok_sources(self.remoteok_sources)

    jobicy_sources: list[str] = []

    @property
    def jobicy_source_configs(self) -> list[JobicyConfig]:
        """Return parsed Jobicy source configurations."""
        return parse_jobicy_sources(self.jobicy_sources)

    startup_jobs_sources: list[str] = []

    @property
    def startup_jobs_source_configs(self) -> list[StartupJobsConfig]:
        """Return parsed Startup Jobs RSS role configurations."""
        return parse_startup_jobs_sources(self.startup_jobs_sources)

    hopin_sources: list[str] = []

    @property
    def hopin_source_configs(self) -> list[HopinConfig]:
        """Return parsed Hopin source configurations."""
        return parse_hopin_sources(self.hopin_sources)

    fourdayweek_sources: list[str] = []

    @property
    def fourdayweek_source_configs(self) -> list[FourDayWeekConfig]:
        """Return parsed 4dayweek.io source configurations."""
        return parse_fourdayweek_sources(self.fourdayweek_sources)



    ayla_sources: list[str] = []

    @property
    def ayla_source_configs(self) -> list[AylaConfig]:
        """Return parsed AylaGov source configurations."""
        return parse_ayla_sources(self.ayla_sources)


    arbeitnow_sources: list[str] = []

    @property
    def arbeitnow_source_configs(self) -> list[ArbeitnowConfig]:
        """Return parsed Arbeitnow source configurations."""
        return parse_arbeitnow_sources(self.arbeitnow_sources)


    workable_sources: list[str] = []

    @property
    def workable_source_configs(self) -> list[WorkableConfig]:
        """Return parsed Workable career-account configurations."""
        return parse_workable_sources(self.workable_sources)


    rippling_sources: list[str] = []

    @property
    def rippling_source_configs(self) -> list[RipplingConfig]:
        """Return parsed Rippling career-board configurations."""
        return parse_rippling_sources(self.rippling_sources)

    workday_sources: list[str] = []

    @property
    def workday_source_configs(self) -> list[WorkdayConfig]:
        """Return parsed Workday career-board configurations."""
        return parse_workday_sources(self.workday_sources)

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
