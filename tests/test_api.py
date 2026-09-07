from collections.abc import Generator
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from pydantic import HttpUrl
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.main import app, get_db
from packages.domain.job import Job
from packages.persistence.models import Base
from packages.persistence.sqlalchemy_job_repository import (
    SQLAlchemyJobRepository,
)

TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)

Base.metadata.create_all(bind=test_engine)


def override_get_db() -> Generator[Session, None, None]:
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_jobs_returns_empty_list() -> None:
    response = client.get("/jobs")

    assert response.status_code == 200
    assert response.json() == []


def test_list_jobs_returns_relevance_information() -> None:
    session = TestSessionLocal()

    try:
        repository = SQLAlchemyJobRepository(session)

        repository.save(
            Job(
                title="Hardware Design Engineer",
                company="Test Electronics",
                location="Bangalore",
                description=(
                    "Design embedded hardware, PCB layouts, "
                    "and electronic circuits."
                ),
                source="test",
                source_job_id="relevance-001",
                source_url=HttpUrl("https://example.com/jobs/relevance-001"),
                skills=["PCB", "Altium"],
                discovered_at=datetime.now(timezone.utc),
            )
        )
    finally:
        session.close()

    response = client.get("/jobs")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    job = data[0]

    assert job["title"] == "Hardware Design Engineer"
    assert job["company"] == "Test Electronics"

    assert job["relevance"]["is_relevant"] is True
    assert job["relevance"]["score"] > 0
    assert "title:hardware design engineer" in job["relevance"]["reasons"]
