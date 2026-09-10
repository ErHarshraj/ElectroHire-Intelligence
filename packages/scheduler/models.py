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
