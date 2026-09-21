from packages.common.config import Settings
from packages.common.hopin_config import HopinConfig, parse_hopin_sources


def test_parse_hopin_sources() -> None:
    configs = parse_hopin_sources(
        [
            "jobs|Technology|India|||false",
            "internships|Technology|India|||false",
        ]
    )

    assert configs == [
        HopinConfig(
            endpoint="jobs",
            industry="Technology",
            location="India",
            work_type=None,
            role_type=None,
            unofficial=False,
        ),
        HopinConfig(
            endpoint="internships",
            industry="Technology",
            location="India",
            work_type=None,
            role_type=None,
            unofficial=False,
        ),
    ]


def test_settings_build_hopin_source_configs() -> None:
    settings = Settings(
        hopin_sources=[
            "jobs|Technology|India|||false",
        ]
    )

    assert settings.hopin_source_configs == [
        HopinConfig(
            endpoint="jobs",
            industry="Technology",
            location="India",
            work_type=None,
            role_type=None,
            unofficial=False,
        )
    ]
