from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

from packages.application.models import ApplicationMethod
from packages.matching.decision import DecisionAction


class ApplicationExecutionAction(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"


@dataclass(frozen=True)
class ApplicationExecutionResult:
    action: ApplicationExecutionAction
    reason: str


class ApplicationExecutionPolicy:
    """Decide whether an application attempt is permitted to execute."""

    def evaluate(
        self,
        decision_action: DecisionAction,
        application_method: ApplicationMethod,
        target_value: str | None,
        already_submitted: bool,
        active_attempt: bool,
    ) -> ApplicationExecutionResult:
        if decision_action != DecisionAction.APPLY:
            return ApplicationExecutionResult(
                action=ApplicationExecutionAction.BLOCK,
                reason="decision does not permit automatic application",
            )

        if already_submitted:
            return ApplicationExecutionResult(
                action=ApplicationExecutionAction.BLOCK,
                reason="job already has a submitted application",
            )

        if active_attempt:
            return ApplicationExecutionResult(
                action=ApplicationExecutionAction.BLOCK,
                reason="job already has an active application attempt",
            )

        if not target_value:
            return ApplicationExecutionResult(
                action=ApplicationExecutionAction.BLOCK,
                reason="application target is missing",
            )

        if application_method == ApplicationMethod.EMAIL:
            if not self._is_valid_email(target_value):
                return ApplicationExecutionResult(
                    action=ApplicationExecutionAction.BLOCK,
                    reason="email application target is invalid",
                )

        elif application_method == ApplicationMethod.BROWSER:
            if not self._is_valid_url(target_value):
                return ApplicationExecutionResult(
                    action=ApplicationExecutionAction.BLOCK,
                    reason="browser application target is invalid",
                )

        else:
            return ApplicationExecutionResult(
                action=ApplicationExecutionAction.BLOCK,
                reason="application method is invalid",
            )

        return ApplicationExecutionResult(
            action=ApplicationExecutionAction.ALLOW,
            reason="application is eligible for execution",
        )

    @staticmethod
    def _is_valid_email(value: str) -> bool:
        if "@" not in value:
            return False

        local, domain = value.rsplit("@", 1)

        if not local or not domain:
            return False

        if "." not in domain:
            return False

        if domain.startswith(".") or domain.endswith("."):
            return False

        return True

    @staticmethod
    def _is_valid_url(value: str) -> bool:
        parsed = urlparse(value)

        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
        )
