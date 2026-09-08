import pytest

from apps.worker.main import process_source, run
from packages.common.config import get_settings
from packages.job_sources.mock import MockJobSource
from packages.persistence.in_memory import InMemoryJobRepository
from packages.persistence.in_memory_decision import InMemoryDecisionRepository


def test_worker_requires_adzuna_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_settings.cache_clear()

    monkeypatch.setenv("ADZUNA_APP_ID", "")
    monkeypatch.setenv("ADZUNA_APP_KEY", "")

    with pytest.raises(
        RuntimeError,
        match="Adzuna credentials are not configured",
    ):
        run()

    get_settings.cache_clear()


def test_process_source_evaluates_new_jobs() -> None:
    source = MockJobSource()
    repository = InMemoryJobRepository()
    decision_repository = InMemoryDecisionRepository()

    new_count, evaluated_count, ignored_count = process_source(
        source=source,
        repository=repository,
        decision_repository=decision_repository,
    )

    assert new_count == 2
    assert evaluated_count == 2
    assert ignored_count == 0

    assert len(decision_repository.decisions) == 2


def test_process_source_persists_decisions() -> None:
    source = MockJobSource()
    repository = InMemoryJobRepository()
    decision_repository = InMemoryDecisionRepository()

    process_source(
        source=source,
        repository=repository,
        decision_repository=decision_repository,
    )

    decisions = decision_repository.decisions

    assert len(decisions) == 2

    for decision in decisions:
        assert decision.action.value in {"apply", "alert", "ignore"}
        assert 0.0 <= decision.relevance_score <= 100.0
        assert 0.0 <= decision.ranking_score <= 100.0
        assert decision.priority in {
            "HIGH",
            "MEDIUM",
            "LOW",
            "VERY_LOW",
        }
        assert decision.reasons


def test_process_source_does_not_reprocess_duplicates() -> None:
    source = MockJobSource()
    repository = InMemoryJobRepository()
    decision_repository = InMemoryDecisionRepository()

    first_result = process_source(
        source=source,
        repository=repository,
        decision_repository=decision_repository,
    )

    second_result = process_source(
        source=source,
        repository=repository,
        decision_repository=decision_repository,
    )

    assert first_result == (2, 2, 0)
    assert second_result == (0, 0, 0)

    assert len(decision_repository.decisions) == 2
