from datetime import datetime, timezone

from pydantic import HttpUrl

from packages.domain.job import Job
from packages.matching.relevance import JobRelevanceEngine


def make_job(
    title: str,
    description: str = "",
) -> Job:
    """Create a minimal job for relevance testing."""

    return Job(
        title=title,
        company="Test Company",
        location="India",
        description=description,
        source="test",
        source_job_id="123",
        source_url=HttpUrl("https://example.com/job"),
        discovered_at=datetime.now(timezone.utc),
    )


def test_hardware_job_is_relevant() -> None:
    engine = JobRelevanceEngine()

    job = make_job(
        "Embedded Hardware Engineer",
        "Design PCB circuits and work with microcontrollers.",
    )

    result = engine.evaluate(job)

    assert result.is_relevant is True
    assert result.score >= 30
    assert "title:embedded hardware engineer" in result.reasons
    assert "description:pcb" in result.reasons
    assert "description:microcontroller" in result.reasons


def test_account_manager_is_not_relevant() -> None:
    engine = JobRelevanceEngine()

    job = make_job(
        "Senior Account Manager",
        "Manage customer accounts and sales activities.",
    )

    result = engine.evaluate(job)

    assert result.is_relevant is False
    assert "title:-account manager" in result.reasons
    assert "description:-sales" not in result.reasons


def test_electronics_job_is_relevant() -> None:
    engine = JobRelevanceEngine()

    job = make_job(
        "Electronics Design Engineer",
        "Circuit design and electronics development.",
    )

    result = engine.evaluate(job)

    assert result.is_relevant is True
    assert "title:electronics design engineer" in result.reasons
    assert "description:electronics" in result.reasons
    assert "description:circuit design" in result.reasons


def test_specific_title_phrase_prevents_keyword_double_counting() -> None:
    engine = JobRelevanceEngine()

    job = make_job("Embedded Hardware Engineer")

    result = engine.evaluate(job)

    assert result.score == 45.0
    assert result.reasons == ["title:embedded hardware engineer"]


def test_pcb_design_title_variations_are_relevant() -> None:
    engine = JobRelevanceEngine()

    titles = [
        "Engineer - PCB Design",
        "Lead Engineer - PCB Design",
        "Staff Engineer - PCB Design",
        "Lead PCB Design & Development Engineer",
    ]

    for title in titles:
        result = engine.evaluate(make_job(title))

        assert result.is_relevant is True
        assert result.score >= 42.0
        assert "title:pcb design engineer" in result.reasons




def test_digital_hardware_titles_are_relevant() -> None:
    engine = JobRelevanceEngine()

    cases = [
        (
            "Principal Engineer - ASIC Design",
            "ASIC design, circuit architecture, tapeout and chip testing.",
        ),
        (
            "Verification Lead",
            "Verify next-generation ASIC and FPGA designs using testbenches.",
        ),
        (
            "RTL Design Engineer Role",
            "RTL design using Verilog and SystemVerilog for ASIC and SoC development.",
        ),
        (
            "BMC/OpenBMC Firmware Lead Engineer",
            "Firmware development for embedded server hardware and OpenBMC.",
        ),
    ]

    for title, description in cases:
        result = engine.evaluate(make_job(title, description))

        assert result.is_relevant is True
        assert result.score >= 30.0


def test_generic_design_engineer_with_hardware_signals_is_relevant() -> None:
    engine = JobRelevanceEngine()

    job = make_job(
        "Design Engineer",
        (
            "Design analog and digital circuits. Perform OPAMP calculations "
            "and PCB layout and design during end-to-end product development."
        ),
    )

    result = engine.evaluate(job)

    assert result.is_relevant is True
    assert result.score >= 30.0


def test_non_target_engineering_roles_remain_irrelevant() -> None:
    engine = JobRelevanceEngine()

    cases = [
        (
            "Lead Engineer - Functional Safety Manager",
            "Manage functional safety activities for automotive embedded software.",
        ),
        (
            "Robotic Software Engineer",
            "Develop autonomy, perception and path planning software.",
        ),
        (
            "Assistant Professor - ECE",
            "Teach electronics and communication engineering students.",
        ),
        (
            "BIM Modeler",
            "Develop electrical BIM models using Revit.",
        ),
        (
            "Staff Technical Program Manager - Electronics",
            "Manage electronics engineering programs and coordinate technical teams.",
        ),
    ]

    for title, description in cases:
        result = engine.evaluate(make_job(title, description))

        assert result.is_relevant is False
