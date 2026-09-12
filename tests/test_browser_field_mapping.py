from packages.application.browser.field_classifier import (
    BrowserFieldClassification,
    BrowserFieldKind,
)
from packages.application.browser.field_inspector import BrowserField
from packages.application.browser.field_mapping import BrowserFieldMapper
from packages.application.profile import CandidateProfile


def make_field(
    *,
    element: str = "input",
    field_type: str = "text",
    name: str | None = None,
    label: str | None = None,
) -> BrowserField:
    return BrowserField(
        element=element,
        field_type=field_type,
        name=name,
        field_id=None,
        label=label,
        autocomplete=None,
        required=False,
        placeholder=None,
        value=None,
    )


def make_classification(
    kind: BrowserFieldKind,
    *,
    field: BrowserField | None = None,
) -> BrowserFieldClassification:
    return BrowserFieldClassification(
        field=field or make_field(),
        kind=kind,
        confidence=1.0,
        reason="test classification",
    )


def make_profile(
    *,
    full_name: str = "Harshraj",
    email: str = "harshraj@example.com",
    phone: str = "+919999999999",
    resume_path: str | None = "/tmp/resume.pdf",
    experience_level: str = "fresher",
) -> CandidateProfile:
    return CandidateProfile(
        full_name=full_name,
        email=email,
        phone=phone,
        location="India",
        resume_path=resume_path,
        linkedin_url="https://linkedin.com/in/harshraj",
        github_url="https://github.com/ErHarshraj",
        portfolio_url="",
        education=["Electrical and Electronics Engineering"],
        skills=["Embedded C", "ESP-IDF", "PCB Design"],
        projects=["ElectroHire Intelligence"],
        application_answers={
            "experience_level": experience_level,
        },
    )


def test_maps_full_name() -> None:
    mapper = BrowserFieldMapper()

    result = mapper.map(
        make_classification(BrowserFieldKind.FULL_NAME),
        make_profile(),
    )

    assert result.mappable is True
    assert result.value == "Harshraj"
    assert result.source == "full_name"


def test_maps_email() -> None:
    mapper = BrowserFieldMapper()

    result = mapper.map(
        make_classification(BrowserFieldKind.EMAIL),
        make_profile(),
    )

    assert result.mappable is True
    assert result.value == "harshraj@example.com"
    assert result.source == "email"


def test_maps_phone() -> None:
    mapper = BrowserFieldMapper()

    result = mapper.map(
        make_classification(BrowserFieldKind.PHONE),
        make_profile(),
    )

    assert result.mappable is True
    assert result.value == "+919999999999"
    assert result.source == "phone"


def test_maps_resume_path() -> None:
    mapper = BrowserFieldMapper()

    result = mapper.map(
        make_classification(
            BrowserFieldKind.RESUME,
            field=make_field(
                field_type="file",
                name="resume",
            ),
        ),
        make_profile(),
    )

    assert result.mappable is True
    assert result.value == "/tmp/resume.pdf"
    assert result.source == "resume_path"


def test_experience_level_comes_from_application_answers() -> None:
    mapper = BrowserFieldMapper()

    result = mapper.map(
        make_classification(
            BrowserFieldKind.EXPERIENCE_LEVEL,
            field=make_field(
                element="select",
                name="experience_level",
            ),
        ),
        make_profile(),
    )

    assert result.mappable is True
    assert result.value == "fresher"
    assert result.source == "application_answers.experience_level"


def test_missing_experience_answer_is_not_guessed() -> None:
    mapper = BrowserFieldMapper()

    profile = make_profile(experience_level="")

    result = mapper.map(
        make_classification(BrowserFieldKind.EXPERIENCE_LEVEL),
        profile,
    )

    assert result.mappable is False
    assert result.value is None
    assert "candidate value is missing" in result.reason


def test_cover_letter_is_not_automatically_generated() -> None:
    mapper = BrowserFieldMapper()

    result = mapper.map(
        make_classification(BrowserFieldKind.COVER_LETTER),
        make_profile(),
    )

    assert result.mappable is False
    assert result.value is None
    assert result.source == "generated_cover_letter"
    assert "generated application content" in result.reason


def test_submit_control_is_never_mapped() -> None:
    mapper = BrowserFieldMapper()

    result = mapper.map(
        make_classification(
            BrowserFieldKind.SUBMIT,
            field=make_field(
                element="button",
                field_type="submit",
                label="Submit Application",
            ),
        ),
        make_profile(),
    )

    assert result.mappable is False
    assert result.value is None
    assert result.source is None
    assert "never mapped" in result.reason


def test_unknown_field_is_not_mapped() -> None:
    mapper = BrowserFieldMapper()

    result = mapper.map(
        make_classification(BrowserFieldKind.UNKNOWN),
        make_profile(),
    )

    assert result.mappable is False
    assert result.value is None
    assert result.source is None
    assert "no deterministic profile mapping" in result.reason


def test_missing_resume_is_not_mapped() -> None:
    mapper = BrowserFieldMapper()

    profile = make_profile(resume_path=None)

    result = mapper.map(
        make_classification(BrowserFieldKind.RESUME),
        profile,
    )

    assert result.mappable is False
    assert result.value is None
    assert result.source == "resume_path"
    assert "candidate value is missing" in result.reason


def test_missing_phone_is_not_mapped() -> None:
    mapper = BrowserFieldMapper()

    profile = make_profile(phone="")

    result = mapper.map(
        make_classification(BrowserFieldKind.PHONE),
        profile,
    )

    assert result.mappable is False
    assert result.value is None
    assert result.source == "phone"
    assert "candidate value is missing" in result.reason


def test_map_all_preserves_field_order() -> None:
    mapper = BrowserFieldMapper()
    profile = make_profile()

    classifications = [
        make_classification(BrowserFieldKind.FULL_NAME),
        make_classification(BrowserFieldKind.EMAIL),
        make_classification(BrowserFieldKind.PHONE),
        make_classification(BrowserFieldKind.UNKNOWN),
    ]

    results = mapper.map_all(classifications, profile)

    assert [result.field.kind for result in results] == [
        BrowserFieldKind.FULL_NAME,
        BrowserFieldKind.EMAIL,
        BrowserFieldKind.PHONE,
        BrowserFieldKind.UNKNOWN,
    ]

    assert [result.value for result in results] == [
        "Harshraj",
        "harshraj@example.com",
        "+919999999999",
        None,
    ]
