from dataclasses import dataclass, field


@dataclass(frozen=True)
class CandidateProfile:
    """Technical profile used to rank job opportunities."""

    target_roles: tuple[str, ...] = (
        "hardware design engineer",
        "hardware engineer",
        "embedded hardware engineer",
        "pcb design engineer",
        "electronics engineer",
        "embedded systems engineer",
        "robotics hardware engineer",
        "robotics engineer",
        "robotic engineer",
        "iot hardware engineer",
        "drone hardware engineer",
    )

    role_families: tuple[tuple[str, tuple[str, ...], float], ...] = (
        (
            "hardware",
            (
                "hardware engineer",
                "hardware design",
                "hardware development",
                "hardware designer",
                "hardware design engineer",
            ),
            22.0,
        ),
        (
            "embedded",
            (
                "embedded systems engineer",
                "embedded system engineer",
                "embedded hardware",
                "embedded engineer",
            ),
            22.0,
        ),
        (
            "pcb",
            (
                "pcb design",
                "pcb layout",
                "printed circuit board",
                "board design",
                "pcb designer",
                "pcb design engineer",
                "pcb layout engineer",
            ),
            22.0,
        ),
        (
            "electronics",
            (
                "electronics engineer",
                "electronics design",
                "electronics hardware",
                "electronic design",
                "electronics design engineer",
            ),
            20.0,
        ),
        (
            "firmware",
            (
                "firmware engineer",
                "embedded firmware",
                "firmware development",
                "firmware developer",
            ),
            18.0,
        ),
        (
            "robotics",
            (
                "robotics engineer",
                "robotic engineer",
                "robotics hardware",
                "robotic hardware",
                "robotics design",
            ),
            18.0,
        ),
        (
            "electrical",
            (
                "electrical engineer",
                "electrical design",
                "electrical development",
                "electrical design engineer",
                "electrical development engineer",
            ),
            16.0,
        ),
        (
            "rtl_asic",
            (
                "rtl design",
                "asic design",
                "rtl engineer",
                "asic engineer",
                "fpga design",
                "digital design",
            ),
            15.0,
        ),
        (
            "verification",
            (
                "verification engineer",
                "verification lead",
                "design verification",
                "hardware verification",
                "rtl verification",
            ),
            14.0,
        ),
    )

    skill_families: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("embedded_c", ("embedded c", "embedded-c", "c programming")),
        (
            "pcb",
            (
                "pcb design",
                "pcb layout",
                "printed circuit board",
                "board design",
            ),
        ),
        (
            "circuit",
            (
                "circuit design",
                "schematic design",
                "schematics",
            ),
        ),
        (
            "eda",
            (
                "kicad",
                "altium",
                "orcad",
                "cadence",
            ),
        ),
        (
            "microcontroller",
            (
                "stm32",
                "esp32",
                "microcontroller",
                "microcontroller unit",
                "mcu",
            ),
        ),
        (
            "embedded",
            (
                "embedded systems",
                "embedded system",
                "embedded hardware",
                "embedded firmware",
                "firmware",
            ),
        ),
        (
            "electronics",
            (
                "electronics",
                "electronic design",
                "electronics design",
            ),
        ),
        (
            "hardware",
            (
                "hardware design",
                "hardware development",
                "hardware engineering",
            ),
        ),
        (
            "electrical",
            (
                "electrical design",
                "electrical development",
                "electrical engineering",
            ),
        ),
        (
            "rtl",
            (
                "rtl",
                "asic",
                "fpga",
                "verilog",
                "systemverilog",
            ),
        ),
        (
            "verification",
            (
                "verification",
                "validation",
            ),
        ),
        (
            "robotics",
            (
                "robotics",
                "robotic",
            ),
        ),
    )

    domain_families: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "embedded",
            (
                "embedded",
                "firmware",
                "microcontroller",
                "bmc",
                "openbmc",
            ),
        ),
        (
            "robotics",
            (
                "robotics",
                "robotic",
            ),
        ),
        (
            "iot",
            (
                "iot",
                "internet of things",
            ),
        ),
        (
            "drone",
            (
                "drone",
                "uav",
                "unmanned aerial",
            ),
        ),
        (
            "electronics",
            (
                "electronics",
                "electronic",
            ),
        ),
        (
            "semiconductor",
            (
                "semiconductor",
                "asic",
                "rtl",
                "fpga",
                "chip design",
            ),
        ),
        (
            "power_electronics",
            (
                "power electronics",
                "power converter",
                "inverter",
            ),
        ),
        (
            "pcb",
            (
                "pcb",
                "printed circuit board",
                "board layout",
            ),
        ),
        (
            "hardware",
            (
                "hardware",
                "embedded hardware",
            ),
        ),
    )

    experience_keywords: tuple[str, ...] = field(
        default_factory=lambda: (
            "entry level",
            "junior",
            "fresher",
            "graduate",
            "0-1",
            "0-2",
            "1-2",
        )
    )
