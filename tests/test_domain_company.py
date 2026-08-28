from pydantic import HttpUrl

from packages.domain.company import Company


def test_company_creation() -> None:
    company = Company(
        name="Example Electronics",
        description="Embedded and electronics engineering company.",
        website_url=HttpUrl("https://example.com"),
        careers_url=HttpUrl("https://example.com/careers"),
        industry="Electronics",
        location="Bengaluru, India",
        employee_count=150,
        is_startup=True,
        technologies=["STM32", "PCB Design", "Embedded C"],
        discovered_from=["company_careers"],
    )

    assert company.name == "Example Electronics"
    assert company.industry == "Electronics"
    assert company.is_startup is True
    assert company.employee_count == 150
    assert "STM32" in company.technologies
    assert "company_careers" in company.discovered_from
