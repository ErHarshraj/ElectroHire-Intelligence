from datetime import datetime

from packages.domain.job import Job
from packages.matching.ranking import JobRankingEngine


def make_job(
    title: str,
    description: str = "",
    skills: list[str] | None = None,
    experience: str | None = None,
) -> Job:
    from datetime import datetime, timezone

    return Job(
        title=title,
        company="Test Company",
        description=description,
        source="test",
        source_job_id=title,
        source_url="https://example.com/job",
        skills=skills or [],
        experience_required=experience,
        discovered_at=datetime.now(timezone.utc),
    )


def test_strong_hardware_role_is_high_priority() -> None:
    job = make_job(
        "Embedded Hardware Engineer",
        description=(
            "Design embedded hardware, schematics and circuits "
            "for STM32 products."
        ),
        skills=[
            "Embedded C",
            "PCB Design",
            "STM32",
            "KiCad",
        ],
        experience="0-2 years",
    )

    result = JobRankingEngine().rank(job)

    assert result.score >= 80
    assert result.priority == "HIGH"


def test_pcb_layout_is_not_ranked_zero() -> None:
    job = make_job(
        "PCB Layout Design Engineer",
        description=(
            "PCB layout and printed circuit board development "
            "using Altium."
        ),
        skills=["PCB Layout", "Altium"],
    )

    result = JobRankingEngine().rank(job)

    assert result.score >= 40
    assert result.priority in {"LOW", "MEDIUM", "HIGH"}


def test_firmware_role_is_not_ranked_zero() -> None:
    job = make_job(
        "Firmware Engineer",
        description=(
            "Embedded firmware development for microcontroller "
            "based electronics."
        ),
        skills=["Embedded C", "STM32"],
    )

    result = JobRankingEngine().rank(job)

    assert result.score >= 40


def test_rtl_role_gets_adjacent_technical_score() -> None:
    job = make_job(
        "RTL Design Engineer",
        description=(
            "RTL and ASIC design using Verilog for semiconductor "
            "products."
        ),
        skills=["RTL", "ASIC", "Verilog"],
    )

    result = JobRankingEngine().rank(job)

    assert result.score >= 40
    assert result.score < 80


def test_embedded_firmware_family_is_explainable() -> None:
    job = make_job(
        "OpenBMC Firmware Engineer",
        description="Embedded firmware development for BMC systems.",
        skills=["Embedded C", "OpenBMC"],
    )

    result = JobRankingEngine().rank(job)

    assert any(
        "firmware" in reason.lower()
        for reason in result.reasons
    )

    assert any(
        "embedded" in reason.lower()
        for reason in result.reasons
    )


def test_irrelevant_sales_role_cannot_become_high_priority() -> None:
    job = make_job(
        "Senior Account Manager",
        description=(
            "Manage electronics and semiconductor customer accounts."
        ),
        skills=["electronics", "semiconductor"],
    )

    result = JobRankingEngine().rank(job)

    assert result.priority == "VERY_LOW"
    assert result.score <= 35


def test_marketing_manager_is_very_low() -> None:
    job = make_job(
        "Marketing Manager",
        description="Marketing campaigns and customer acquisition.",
    )

    result = JobRankingEngine().rank(job)

    assert result.score < 40
    assert result.priority == "VERY_LOW"


def test_ranking_result_contains_explainable_reasons() -> None:
    job = make_job(
        "Hardware Design Engineer",
        description="Hardware design and PCB development.",
        skills=["PCB Design", "Circuit Design"],
        experience="Junior",
    )

    result = JobRankingEngine().rank(job)

    assert result.reasons
    assert any(
        "relevance" in reason.lower()
        for reason in result.reasons
    )
    assert any(
        "role" in reason.lower()
        for reason in result.reasons
    )


def test_compound_firmware_engineer_title_is_recognized() -> None:
    job = Job(
        title="BMC/OpenBMC Firmware Lead Engineer",
        company="Jabil",
        location="India",
        description="Firmware development and embedded systems engineering.",
        source="test",
        source_job_id="firmware-lead-1",
        source_url="https://example.com/firmware-lead-1",
        skills=["Embedded C", "Firmware", "OpenBMC"],
        discovered_at=datetime.now(),
    )

    result = JobRankingEngine().rank(job)

    assert result.score > 0
    assert any("firmware" in reason.lower() for reason in result.reasons)


def test_robotic_hardware_compound_title_is_recognized() -> None:
    job = Job(
        title="Robotic Engineer-Hardware",
        company="FCI CCM",
        location="India",
        description="Robotics hardware development and electronics.",
        source="test",
        source_job_id="robotic-hardware-1",
        source_url="https://example.com/robotic-hardware-1",
        skills=["Hardware Design", "Electronics", "Robotics"],
        discovered_at=datetime.now(),
    )

    result = JobRankingEngine().rank(job)

    assert result.score > 0
    assert any("robotics" in reason.lower() for reason in result.reasons)
    assert any("hardware" in reason.lower() for reason in result.reasons)


def test_electrical_design_family_is_recognized() -> None:
    job = Job(
        title="Electrical Design & Development Engineer",
        company="HCLTech",
        location="India",
        description="Electrical design and electronics development.",
        source="test",
        source_job_id="electrical-design-1",
        source_url="https://example.com/electrical-design-1",
        skills=["Electrical Design", "Electronics"],
        discovered_at=datetime.now(),
    )

    result = JobRankingEngine().rank(job)

    assert result.score > 0
    assert any("electrical" in reason.lower() for reason in result.reasons)


def test_verification_role_is_recognized_as_adjacent_technical_role() -> None:
    job = Job(
        title="Verification Lead",
        company="ACL Digital",
        location="India",
        description="Hardware verification and RTL verification.",
        source="test",
        source_job_id="verification-lead-1",
        source_url="https://example.com/verification-lead-1",
        skills=["RTL", "Verilog", "Verification"],
        discovered_at=datetime.now(),
    )

    result = JobRankingEngine().rank(job)

    assert result.score > 0
    assert any("verification" in reason.lower() for reason in result.reasons)
