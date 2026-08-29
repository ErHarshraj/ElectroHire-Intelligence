import pytest

from apps.worker.main import run
from packages.common.config import get_settings


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
