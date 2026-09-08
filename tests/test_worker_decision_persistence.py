from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from apps.worker.main import process_source
from packages.job_sources.mock import MockJobSource
from packages.persistence.models import Base
from packages.persistence.sqlalchemy_decision_repository import (
    SQLAlchemyDecisionRepository,
)
from packages.persistence.sqlalchemy_job_repository import (
    SQLAlchemyJobRepository,
)


def test_worker_persists_decisions_with_sqlalchemy() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        job_repository = SQLAlchemyJobRepository(session)
        decision_repository = SQLAlchemyDecisionRepository(session)

        result = process_source(
            source=MockJobSource(),
            repository=job_repository,
            decision_repository=decision_repository,
        )

        assert result == (2, 2, 0)

        jobs = job_repository.list_jobs()

        assert len(jobs) == 2

        for job in jobs:
            assert job.source_job_id is not None

            decisions = decision_repository.list_for_job(
                source=job.source,
                source_job_id=job.source_job_id,
            )

            assert len(decisions) == 1
            assert decisions[0].action.value in {
                "apply",
                "alert",
                "ignore",
            }
            assert 0.0 <= decisions[0].relevance_score <= 100.0
            assert 0.0 <= decisions[0].ranking_score <= 100.0
            assert decisions[0].priority in {
                "HIGH",
                "MEDIUM",
                "LOW",
                "VERY_LOW",
            }
            assert decisions[0].reasons
