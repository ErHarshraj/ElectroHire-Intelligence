import pytest

from packages.application.career_models import (
    CareerApplicationStatus,
    InvalidCareerApplicationTransition,
    validate_career_application_transition,
)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (
            CareerApplicationStatus.SHORTLISTED,
            CareerApplicationStatus.APPLIED,
        ),
        (
            CareerApplicationStatus.APPLIED,
            CareerApplicationStatus.SCREENING,
        ),
        (
            CareerApplicationStatus.SCREENING,
            CareerApplicationStatus.INTERVIEW,
        ),
        (
            CareerApplicationStatus.INTERVIEW,
            CareerApplicationStatus.TECHNICAL,
        ),
        (
            CareerApplicationStatus.INTERVIEW,
            CareerApplicationStatus.OFFER,
        ),
        (
            CareerApplicationStatus.TECHNICAL,
            CareerApplicationStatus.OFFER,
        ),
        (
            CareerApplicationStatus.APPLIED,
            CareerApplicationStatus.REJECTED,
        ),
        (
            CareerApplicationStatus.SCREENING,
            CareerApplicationStatus.WITHDRAWN,
        ),
        (
            CareerApplicationStatus.INTERVIEW,
            CareerApplicationStatus.EXPIRED,
        ),
    ],
)
def test_valid_transition(
    current: CareerApplicationStatus,
    target: CareerApplicationStatus,
) -> None:
    validate_career_application_transition(current, target)


@pytest.mark.parametrize(
    "status",
    list(CareerApplicationStatus),
)
def test_same_status_is_allowed(
    status: CareerApplicationStatus,
) -> None:
    validate_career_application_transition(status, status)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (
            CareerApplicationStatus.SHORTLISTED,
            CareerApplicationStatus.SCREENING,
        ),
        (
            CareerApplicationStatus.APPLIED,
            CareerApplicationStatus.INTERVIEW,
        ),
        (
            CareerApplicationStatus.SCREENING,
            CareerApplicationStatus.OFFER,
        ),
        (
            CareerApplicationStatus.OFFER,
            CareerApplicationStatus.APPLIED,
        ),
        (
            CareerApplicationStatus.REJECTED,
            CareerApplicationStatus.APPLIED,
        ),
        (
            CareerApplicationStatus.WITHDRAWN,
            CareerApplicationStatus.INTERVIEW,
        ),
        (
            CareerApplicationStatus.EXPIRED,
            CareerApplicationStatus.APPLIED,
        ),
    ],
)
def test_invalid_transition_raises(
    current: CareerApplicationStatus,
    target: CareerApplicationStatus,
) -> None:
    with pytest.raises(InvalidCareerApplicationTransition):
        validate_career_application_transition(current, target)


@pytest.mark.parametrize(
    "terminal_status",
    [
        CareerApplicationStatus.OFFER,
        CareerApplicationStatus.REJECTED,
        CareerApplicationStatus.WITHDRAWN,
        CareerApplicationStatus.EXPIRED,
    ],
)
def test_terminal_status_cannot_transition(
    terminal_status: CareerApplicationStatus,
) -> None:
    for target in CareerApplicationStatus:
        if target == terminal_status:
            continue

        with pytest.raises(InvalidCareerApplicationTransition):
            validate_career_application_transition(
                terminal_status,
                target,
            )
