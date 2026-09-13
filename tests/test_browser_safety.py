from packages.application.browser.application_preview import (
    BrowserApplicationPreview,
)
from packages.application.browser.field_classifier import (
    BrowserFieldClassification,
    BrowserFieldKind,
)
from packages.application.browser.field_inspector import BrowserField
from packages.application.browser.safety import (
    BrowserApplicationSafetyGuard,
)


def make_field(
    *,
    field_type: str = "text",
    name: str | None = "full_name",
    field_id: str | None = "full_name",
    label: str | None = "Full Name",
    required: bool = True,
) -> BrowserFieldClassification:
    field = BrowserField(
        element="input",
        field_type=field_type,
        name=name,
        field_id=field_id,
        label=label,
        autocomplete=None,
        required=required,
        placeholder=None,
        value=None,
    )

    return BrowserFieldClassification(
        field=field,
        kind=BrowserFieldKind.FULL_NAME,
        confidence=1.0,
        reason="test",
    )


def make_preview(valid: bool = True) -> BrowserApplicationPreview:
    return BrowserApplicationPreview(
        url="https://example.com/careers/apply",
        title="Application",
        valid=valid,
        fields=[],
        issues=[] if valid else ["test validation failure"],
    )


def test_safety_allows_approved_valid_application() -> None:
    guard = BrowserApplicationSafetyGuard()

    result = guard.evaluate(
        application_url="https://example.com/careers/apply",
        current_url="https://example.com/careers/apply",
        preview=make_preview(),
        fields=[make_field()],
        submit_control_count=1,
        approved=True,
    )

    assert result.allowed is True


def test_safety_requires_explicit_approval() -> None:
    guard = BrowserApplicationSafetyGuard()

    result = guard.evaluate(
        application_url="https://example.com/careers/apply",
        current_url="https://example.com/careers/apply",
        preview=make_preview(),
        fields=[make_field()],
        submit_control_count=1,
        approved=False,
    )

    assert result.allowed is False
    assert "approval" in result.reason


def test_safety_blocks_invalid_preview() -> None:
    guard = BrowserApplicationSafetyGuard()

    result = guard.evaluate(
        application_url="https://example.com/careers/apply",
        current_url="https://example.com/careers/apply",
        preview=make_preview(valid=False),
        fields=[make_field()],
        submit_control_count=1,
        approved=True,
    )

    assert result.allowed is False


def test_safety_blocks_cross_origin_redirect() -> None:
    guard = BrowserApplicationSafetyGuard()

    result = guard.evaluate(
        application_url="https://example.com/careers/apply",
        current_url="https://evil.example/careers/apply",
        preview=make_preview(),
        fields=[make_field()],
        submit_control_count=1,
        approved=True,
    )

    assert result.allowed is False
    assert "different origin" in result.reason


def test_safety_blocks_multiple_submit_controls() -> None:
    guard = BrowserApplicationSafetyGuard()

    result = guard.evaluate(
        application_url="https://example.com/careers/apply",
        current_url="https://example.com/careers/apply",
        preview=make_preview(),
        fields=[make_field()],
        submit_control_count=2,
        approved=True,
    )

    assert result.allowed is False


def test_safety_blocks_password_field() -> None:
    guard = BrowserApplicationSafetyGuard()
    field = make_field(field_type="password")

    result = guard.evaluate(
        application_url="https://example.com/careers/apply",
        current_url="https://example.com/careers/apply",
        preview=make_preview(),
        fields=[field],
        submit_control_count=1,
        approved=True,
    )

    assert result.allowed is False


def test_safety_blocks_captcha_field() -> None:
    guard = BrowserApplicationSafetyGuard()

    field = make_field(
        name="recaptcha_response",
        field_id="recaptcha",
        label="reCAPTCHA",
    )

    result = guard.evaluate(
        application_url="https://example.com/careers/apply",
        current_url="https://example.com/careers/apply",
        preview=make_preview(),
        fields=[field],
        submit_control_count=1,
        approved=True,
    )

    assert result.allowed is False


def test_safety_blocks_unknown_required_field() -> None:
    guard = BrowserApplicationSafetyGuard()

    field = make_field()
    unknown = BrowserFieldClassification(
        field=field.field,
        kind=BrowserFieldKind.UNKNOWN,
        confidence=0.0,
        reason="not recognized",
    )

    result = guard.evaluate(
        application_url="https://example.com/careers/apply",
        current_url="https://example.com/careers/apply",
        preview=make_preview(),
        fields=[unknown],
        submit_control_count=1,
        approved=True,
    )

    assert result.allowed is False
    assert "unknown required" in result.reason
