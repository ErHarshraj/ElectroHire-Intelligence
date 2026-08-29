from collections.abc import Iterable

from packages.domain.job import Job
from packages.job_sources.adzuna.client import AdzunaClient
from packages.job_sources.adzuna.parser import parse_job
from packages.job_sources.base import JobSource


class AdzunaJobSource(JobSource):
    """Adzuna-backed implementation of the JobSource interface."""

    name = "adzuna"

    def __init__(
        self,
        client: AdzunaClient,
        query: str,
        pages: int = 1,
    ) -> None:
        self.client = client
        self.query = query
        self.pages = pages

    def fetch_jobs(self) -> Iterable[Job]:
        for page in range(1, self.pages + 1):
            data = self.client.search_jobs(
                query=self.query,
                page=page,
            )

            results = data.get("results", [])

            if not isinstance(results, list):
                raise TypeError("Adzuna results must be a list.")

            for item in results:
                if not isinstance(item, dict):
                    raise TypeError("Adzuna job result must be an object.")

                yield parse_job(item)
