import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.domain.candidate_profile import CandidateProfile
from packages.persistence.candidate_profile_repository import (
    CandidateProfileRepository,
)
from packages.persistence.models import CandidateProfileModel


class SQLAlchemyCandidateProfileRepository(CandidateProfileRepository):
    """SQLAlchemy persistence for the canonical candidate profile."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self) -> CandidateProfile | None:
        """Return the canonical candidate profile."""

        statement = (
            select(CandidateProfileModel)
            .order_by(CandidateProfileModel.id.asc())
            .limit(1)
        )

        model = self.session.scalar(statement)

        if model is None:
            return None

        return self._to_domain(model)

    def save(self, profile: CandidateProfile) -> int:
        """Create or replace the canonical candidate profile."""

        model = None

        if profile.id is not None:
            model = self.session.get(
                CandidateProfileModel,
                profile.id,
            )

        if model is None:
            model = self.session.scalar(
                select(CandidateProfileModel)
                .order_by(CandidateProfileModel.id.asc())
                .limit(1)
            )

        if model is None:
            model = CandidateProfileModel()
            self.session.add(model)

        self._apply(profile, model)

        self.session.flush()
        profile_id = model.id
        self.session.commit()

        return profile_id

    @staticmethod
    def _apply(
        profile: CandidateProfile,
        model: CandidateProfileModel,
    ) -> None:
        """Copy a domain profile into its persistence model."""

        model.full_name = profile.full_name
        model.email = profile.email
        model.phone = profile.phone
        model.location = profile.location
        model.resume_path = profile.resume_path
        model.linkedin_url = profile.linkedin_url
        model.github_url = profile.github_url
        model.portfolio_url = profile.portfolio_url

        model.education = json.dumps(profile.education)
        model.skills = json.dumps(profile.skills)
        model.projects = json.dumps(profile.projects)
        model.application_answers = json.dumps(
            profile.application_answers
        )

        model.target_roles = json.dumps(profile.target_roles)
        model.role_families = json.dumps(profile.role_families)
        model.skill_families = json.dumps(profile.skill_families)
        model.domain_families = json.dumps(profile.domain_families)
        model.experience_keywords = json.dumps(
            profile.experience_keywords
        )

    @staticmethod
    def _to_domain(
        model: CandidateProfileModel,
    ) -> CandidateProfile:
        """Convert a persistence model into the canonical domain profile."""

        role_families = json.loads(model.role_families)
        skill_families = json.loads(model.skill_families)
        domain_families = json.loads(model.domain_families)

        return CandidateProfile(
            id=model.id,
            full_name=model.full_name,
            email=model.email,
            phone=model.phone,
            location=model.location,
            resume_path=model.resume_path,
            linkedin_url=model.linkedin_url,
            github_url=model.github_url,
            portfolio_url=model.portfolio_url,
            education=json.loads(model.education),
            skills=json.loads(model.skills),
            projects=json.loads(model.projects),
            application_answers=json.loads(
                model.application_answers
            ),
            target_roles=tuple(
                json.loads(model.target_roles)
            ),
            role_families=tuple(
                (name, tuple(phrases), float(weight))
                for name, phrases, weight in role_families
            ),
            skill_families=tuple(
                (name, tuple(phrases))
                for name, phrases in skill_families
            ),
            domain_families=tuple(
                (name, tuple(phrases))
                for name, phrases in domain_families
            ),
            experience_keywords=tuple(
                json.loads(model.experience_keywords)
            ),
        )
