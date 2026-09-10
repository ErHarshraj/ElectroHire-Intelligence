from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SchedulerRunResult:
    started_at: datetime
    completed_at: datetime
    success: bool
    message: str


@dataclass(frozen=True)
class SchedulerConfig:
    discovery_interval_minutes: int = 60
    recovery_interval_minutes: int = 30

    def __post_init__(self) -> None:
        if self.discovery_interval_minutes <= 0:
            raise ValueError("discovery interval must be greater than zero")

        if self.recovery_interval_minutes <= 0:
            raise ValueError("recovery interval must be greater than zero")
