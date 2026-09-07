from packages.common.config import get_settings
from packages.ingestion.service import IngestionService
from packages.job_sources.adzuna.client import AdzunaClient
from packages.job_sources.adzuna.source import AdzunaJobSource
from packages.persistence.database import SessionLocal, create_tables
from packages.persistence.sqlalchemy_job_repository import SQLAlchemyJobRepository


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

        total_new_jobs = 0

        for query in settings.adzuna_queries:
            source = AdzunaJobSource(
                client=client,
                query=query,
                pages=settings.adzuna_pages,
            )

            ingestion = IngestionService(
                source=source,
                repository=repository,
            )

            jobs = ingestion.ingest()
            total_new_jobs += len(jobs)

            print(
                f"Query: {query!r} | "
                f"New jobs: {len(jobs)}"
            )

        print(f"Total new jobs: {total_new_jobs}")

    finally:
        session.close()


if __name__ == "__main__":
    run()
