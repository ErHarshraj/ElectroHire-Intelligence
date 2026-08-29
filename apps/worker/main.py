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

        source = AdzunaJobSource(
            client=client,
            query="embedded hardware",
        )

        repository = SQLAlchemyJobRepository(session)

        ingestion = IngestionService(
            source=source,
            repository=repository,
        )

        jobs = ingestion.ingest()

        print(f"Discovered new jobs: {len(jobs)}")

    finally:
        session.close()


if __name__ == "__main__":
    run()
