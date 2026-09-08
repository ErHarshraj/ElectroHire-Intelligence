from packages.common.config import get_settings
from packages.domain.lifecycle import JobLifecycle
from packages.ingestion.service import IngestionService
from packages.job_sources.adzuna.client import AdzunaClient
from packages.job_sources.adzuna.source import AdzunaJobSource
from packages.job_sources.base import JobSource
from packages.matching.decision import JobDecisionEngine
from packages.matching.evaluation import JobEvaluationService
from packages.matching.ranking import JobRankingEngine
from packages.matching.relevance import JobRelevanceEngine
from packages.persistence.database import SessionLocal, create_tables
from packages.persistence.decision_repository import DecisionRepository
from packages.persistence.job_repository import JobRepository
from packages.persistence.sqlalchemy_decision_repository import (
    SQLAlchemyDecisionRepository,
)
from packages.persistence.sqlalchemy_job_repository import SQLAlchemyJobRepository


def process_source(
    source: JobSource,
    repository: JobRepository,
    decision_repository: DecisionRepository,
) -> tuple[int, int, int]:
    """Ingest, evaluate, rank, and decide newly discovered jobs."""

    ingestion = IngestionService(
        source=source,
        repository=repository,
    )

    evaluation = JobEvaluationService(
        relevance_engine=JobRelevanceEngine(),
        lifecycle=JobLifecycle(),
        repository=repository,
    )

    ranking = JobRankingEngine()
    decision = JobDecisionEngine()

    jobs = ingestion.ingest()

    evaluated_count = 0
    ignored_count = 0

    for job in jobs:
        relevance_result = evaluation.evaluate(job)
        ranking_result = ranking.rank(job)
        decision_result = decision.decide(
            job=job,
            relevance=relevance_result,
            ranking=ranking_result,
        )

        if job.source_job_id is None:
            raise ValueError(
                f"Cannot persist decision for job without source_job_id: "
                f"{job.title!r}."
            )

        decision_repository.save(
            source=job.source,
            source_job_id=job.source_job_id,
            action=decision_result.action,
            relevance_score=relevance_result.score,
            ranking_score=ranking_result.score,
            priority=ranking_result.priority,
            reasons=decision_result.reasons,
        )

        if relevance_result.is_relevant:
            evaluated_count += 1
        else:
            ignored_count += 1

        print(
            f"Job: {job.title!r} | "
            f"Score: {ranking_result.score:.1f} | "
            f"Priority: {ranking_result.priority} | "
            f"Decision: {decision_result.action.value}"
        )

    return len(jobs), evaluated_count, ignored_count


def run() -> None:
    settings = get_settings()

    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        raise RuntimeError(
            "Adzuna credentials are not configured. "
            "Set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env."
        )

    create_tables()

    session = SessionLocal()

    try:
        client = AdzunaClient(
            app_id=settings.adzuna_app_id,
            app_key=settings.adzuna_app_key,
            country=settings.adzuna_country,
        )

        repository = SQLAlchemyJobRepository(session)
        decision_repository = SQLAlchemyDecisionRepository(session)

        total_new_jobs = 0
        total_evaluated_jobs = 0
        total_ignored_jobs = 0

        for query in settings.adzuna_queries:
            source = AdzunaJobSource(
                client=client,
                query=query,
                pages=settings.adzuna_pages,
            )

            new_count, evaluated_count, ignored_count = process_source(
                source=source,
                repository=repository,
                decision_repository=decision_repository,
            )

            total_new_jobs += new_count
            total_evaluated_jobs += evaluated_count
            total_ignored_jobs += ignored_count

            print(
                f"Query: {query!r} | "
                f"New jobs: {new_count} | "
                f"Evaluated: {evaluated_count} | "
                f"Ignored: {ignored_count}"
            )

        print(f"Total new jobs: {total_new_jobs}")
        print(f"Total evaluated jobs: {total_evaluated_jobs}")
        print(f"Total ignored jobs: {total_ignored_jobs}")

    finally:
        session.close()


if __name__ == "__main__":
    run()
