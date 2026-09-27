from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from packages.domain.candidate_profile import CandidateProfile
from packages.persistence.models import Base
from packages.persistence.sqlalchemy_candidate_profile_repository import (
    SQLAlchemyCandidateProfileRepository,
)


def make_repository() -> SQLAlchemyCandidateProfileRepository:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    return SQLAlchemyCandidateProfileRepository(
        Session(engine)
    )


def make_profile() -> CandidateProfile:
    return CandidateProfile(
        full_name="Harshraj",
        email="harshraj@example.com",
        phone="9876543210",
        location="Indore, Madhya Pradesh",
        resume_path="resumes/HARSHRAJ_RESUME_Hardware.pdf",
        linkedin_url="https://linkedin.com/in/harshraj",
        github_url="https://github.com/ErHarshraj",
        portfolio_url="https://example.com/portfolio",
        education=["B.Tech Electronics Engineering"],
        skills=["Embedded C", "KiCad", "ESP32"],
        projects=[
            "Gesture LED Control",
            "ElectroHire Intelligence",
        ],
        application_answers={
            "work_authorization": "Yes",
        },
    )


def test_get_missing_profile_returns_none() -> None:
    repository = make_repository()

    assert repository.get() is None


def test_save_and_get_round_trip_preserves_profile() -> None:
    repository = make_repository()
    profile = make_profile()

    profile_id = repository.save(profile)
    restored = repository.get()

    assert restored is not None
    assert restored.id == profile_id
    assert restored.full_name == profile.full_name
    assert restored.email == profile.email
    assert restored.phone == profile.phone
    assert restored.location == profile.location
    assert restored.resume_path == profile.resume_path
    assert restored.linkedin_url == profile.linkedin_url
    assert restored.github_url == profile.github_url
    assert restored.portfolio_url == profile.portfolio_url
    assert restored.education == profile.education
    assert restored.skills == profile.skills
    assert restored.projects == profile.projects
    assert restored.application_answers == profile.application_answers
    assert restored.target_roles == profile.target_roles
    assert restored.role_families == profile.role_families
    assert restored.skill_families == profile.skill_families
    assert restored.domain_families == profile.domain_families
    assert restored.experience_keywords == profile.experience_keywords


def test_save_updates_existing_canonical_profile() -> None:
    repository = make_repository()

    profile_id = repository.save(make_profile())

    updated = CandidateProfile(
        id=profile_id,
        full_name="Updated Candidate",
        email="updated@example.com",
        skills=["STM32", "Altium"],
    )

    updated_id = repository.save(updated)
    restored = repository.get()

    assert updated_id == profile_id
    assert restored is not None
    assert restored.id == profile_id
    assert restored.full_name == "Updated Candidate"
    assert restored.email == "updated@example.com"
    assert restored.skills == ["STM32", "Altium"]


def test_save_does_not_create_multiple_canonical_profiles() -> None:
    repository = make_repository()

    first_id = repository.save(make_profile())
    second_id = repository.save(
        CandidateProfile(full_name="Second Save")
    )

    assert second_id == first_id

    restored = repository.get()

    assert restored is not None
    assert restored.full_name == "Second Save"
