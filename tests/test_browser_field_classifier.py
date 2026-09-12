from packages.application.browser.field_classifier import (
    BrowserFieldClassifier,
    BrowserFieldKind,
)
from packages.application.browser.field_inspector import BrowserField


def make_field(
    *,
    element: str = "input",
    field_type: str = "text",
    name: str | None = None,
    field_id: str | None = None,
    label: str | None = None,
    autocomplete: str | None = None,
    placeholder: str | None = None,
    required: bool = False,
    value: str | None = None,
) -> BrowserField:
    return BrowserField(
        element=element,
        field_type=field_type,
        name=name,
        field_id=field_id,
        label=label,
        autocomplete=autocomplete,
        required=required,
        placeholder=placeholder,
        value=value,
    )


def test_classifies_common_application_fields() -> None:
    classifier = BrowserFieldClassifier()

    fields = [
        make_field(
            name="name",
            field_id="name",
            label="Full Name",
            autocomplete="name",
        ),
        make_field(
            field_type="email",
            name="email",
            field_id="email",
            label="Email",
            autocomplete="email",
        ),
        make_field(
            field_type="tel",
            name="phone",
            field_id="phone",
            label="Phone",
            autocomplete="tel",
        ),
        make_field(
            field_type="file",
            name="resume",
            field_id="resume",
            label="Resume",
        ),
        make_field(
            element="textarea",
            name="cover_letter",
            field_id="cover-letter",
            label="Cover Letter",
        ),
        make_field(
            element="select",
            name="experience",
            field_id="experience",
            label="Experience Level",
        ),
        make_field(
            element="button",
            field_type="submit",
            label="Submit Application",
        ),
    ]

    results = classifier.classify_all(fields)

    assert [result.kind for result in results] == [
        BrowserFieldKind.FULL_NAME,
        BrowserFieldKind.EMAIL,
        BrowserFieldKind.PHONE,
        BrowserFieldKind.RESUME,
        BrowserFieldKind.COVER_LETTER,
        BrowserFieldKind.EXPERIENCE_LEVEL,
        BrowserFieldKind.SUBMIT,
    ]


def test_email_type_is_stronger_than_generic_metadata() -> None:
    classifier = BrowserFieldClassifier()

    field = make_field(
        field_type="email",
        name="contact",
        label="Contact Information",
    )

    result = classifier.classify(field)

    assert result.kind == BrowserFieldKind.EMAIL
    assert result.confidence == 1.0
    assert result.reason == "input type=email"


def test_tel_type_is_stronger_than_generic_metadata() -> None:
    classifier = BrowserFieldClassifier()

    field = make_field(
        field_type="tel",
        name="contact",
        label="Contact Information",
    )

    result = classifier.classify(field)

    assert result.kind == BrowserFieldKind.PHONE
    assert result.confidence == 1.0
    assert result.reason == "input type=tel"


def test_file_input_without_resume_metadata_is_unknown() -> None:
    classifier = BrowserFieldClassifier()

    field = make_field(
        field_type="file",
        name="attachment",
        field_id="upload",
        label="Upload Document",
    )

    result = classifier.classify(field)

    assert result.kind == BrowserFieldKind.UNKNOWN
    assert result.confidence == 0.0
    assert "no deterministic resume/CV signal" in result.reason


def test_unknown_field_is_not_guessed() -> None:
    classifier = BrowserFieldClassifier()

    field = make_field(
        name="custom_field",
        field_id="custom-field",
        label="Additional Information",
    )

    result = classifier.classify(field)

    assert result.kind == BrowserFieldKind.UNKNOWN
    assert result.confidence == 0.0
    assert "no deterministic semantic signal" in result.reason


def test_submit_button_is_classified_from_label() -> None:
    classifier = BrowserFieldClassifier()

    field = make_field(
        element="button",
        field_type="button",
        label="Apply Now",
    )

    result = classifier.classify(field)

    assert result.kind == BrowserFieldKind.SUBMIT
    assert result.confidence == 0.85
