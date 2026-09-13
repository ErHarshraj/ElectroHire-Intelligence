from packages.application.execution_policy import (
    ApplicationExecutionAction,
    ApplicationExecutionPolicy,
)
from packages.application.models import (
    ApplicationExecutionMode,
    ApplicationMethod,
)
from packages.matching.decision import DecisionAction


def test_apply_decision_with_valid_target_is_allowed() -> None:
    policy = ApplicationExecutionPolicy()

    result = policy.evaluate(
        decision_action=DecisionAction.APPLY,
        application_method=ApplicationMethod.EMAIL,
        target_value="recruiter@example.com",
        already_submitted=False,
        active_attempt=False,
        execution_mode=ApplicationExecutionMode.FULL_AUTO,
    )

    assert result.action == ApplicationExecutionAction.ALLOW
    assert result.reason == "application is eligible for full automatic execution"


def test_alert_decision_is_never_allowed() -> None:
    policy = ApplicationExecutionPolicy()

    result = policy.evaluate(
        decision_action=DecisionAction.ALERT,
        application_method=ApplicationMethod.EMAIL,
        target_value="recruiter@example.com",
        already_submitted=False,
        active_attempt=False,
    )

    assert result.action == ApplicationExecutionAction.BLOCK
    assert result.reason == "decision does not permit automatic application"


def test_ignore_decision_is_never_allowed() -> None:
    policy = ApplicationExecutionPolicy()

    result = policy.evaluate(
        decision_action=DecisionAction.IGNORE,
        application_method=ApplicationMethod.EMAIL,
        target_value="recruiter@example.com",
        already_submitted=False,
        active_attempt=False,
    )

    assert result.action == ApplicationExecutionAction.BLOCK
    assert result.reason == "decision does not permit automatic application"


def test_missing_target_blocks_execution() -> None:
    policy = ApplicationExecutionPolicy()

    result = policy.evaluate(
        decision_action=DecisionAction.APPLY,
        application_method=ApplicationMethod.EMAIL,
        target_value=None,
        already_submitted=False,
        active_attempt=False,
    )

    assert result.action == ApplicationExecutionAction.BLOCK
    assert result.reason == "application target is missing"


def test_already_submitted_blocks_execution() -> None:
    policy = ApplicationExecutionPolicy()

    result = policy.evaluate(
        decision_action=DecisionAction.APPLY,
        application_method=ApplicationMethod.EMAIL,
        target_value="recruiter@example.com",
        already_submitted=True,
        active_attempt=False,
    )

    assert result.action == ApplicationExecutionAction.BLOCK
    assert result.reason == "job already has a submitted application"


def test_active_attempt_blocks_execution() -> None:
    policy = ApplicationExecutionPolicy()

    result = policy.evaluate(
        decision_action=DecisionAction.APPLY,
        application_method=ApplicationMethod.EMAIL,
        target_value="recruiter@example.com",
        already_submitted=False,
        active_attempt=True,
    )

    assert result.action == ApplicationExecutionAction.BLOCK
    assert result.reason == "job already has an active application attempt"


def test_browser_target_must_be_a_url() -> None:
    policy = ApplicationExecutionPolicy()

    result = policy.evaluate(
        decision_action=DecisionAction.APPLY,
        application_method=ApplicationMethod.BROWSER,
        target_value="not-a-url",
        already_submitted=False,
        active_attempt=False,
    )

    assert result.action == ApplicationExecutionAction.BLOCK
    assert result.reason == "browser application target is invalid"


def test_email_target_must_contain_valid_email_structure() -> None:
    policy = ApplicationExecutionPolicy()

    result = policy.evaluate(
        decision_action=DecisionAction.APPLY,
        application_method=ApplicationMethod.EMAIL,
        target_value="not-an-email",
        already_submitted=False,
        active_attempt=False,
    )

    assert result.action == ApplicationExecutionAction.BLOCK
    assert result.reason == "email application target is invalid"


def test_dry_run_blocks_submission() -> None:
    policy = ApplicationExecutionPolicy()

    result = policy.evaluate(
        decision_action=DecisionAction.APPLY,
        application_method=ApplicationMethod.EMAIL,
        target_value="recruiter@example.com",
        already_submitted=False,
        active_attempt=False,
    )

    assert result.action == ApplicationExecutionAction.BLOCK
    assert "dry-run" in result.reason


def test_approval_required_blocks_submission() -> None:
    policy = ApplicationExecutionPolicy()

    result = policy.evaluate(
        decision_action=DecisionAction.APPLY,
        application_method=ApplicationMethod.EMAIL,
        target_value="recruiter@example.com",
        already_submitted=False,
        active_attempt=False,
        execution_mode=ApplicationExecutionMode.APPROVAL_REQUIRED,
    )

    assert result.action == ApplicationExecutionAction.BLOCK
    assert "approval" in result.reason


def test_full_auto_allows_submission() -> None:
    policy = ApplicationExecutionPolicy()

    result = policy.evaluate(
        decision_action=DecisionAction.APPLY,
        application_method=ApplicationMethod.EMAIL,
        target_value="recruiter@example.com",
        already_submitted=False,
        active_attempt=False,
        execution_mode=ApplicationExecutionMode.FULL_AUTO,
    )

    assert result.action == ApplicationExecutionAction.ALLOW
    assert "full automatic" in result.reason
