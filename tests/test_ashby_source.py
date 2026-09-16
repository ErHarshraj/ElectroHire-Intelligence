import json

from packages.job_sources.career.ashby import AshbyJobSource


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_ashby_source_parses_public_job():
    payload = {
        "jobs": [
            {
                "title": "Embedded Hardware Engineer",
                "location": "Bengaluru, India",
                "secondaryLocations": ["Remote"],
                "department": "Engineering",
                "team": "Hardware",
                "isListed": True,
                "isRemote": False,
                "workplaceType": "Hybrid",
                "descriptionPlain": (
                    "Design embedded hardware using STM32, "
                    "PCB and I2C."
                ),
                "publishedAt": "2026-09-01T10:00:00.000Z",
                "employmentType": "FullTime",
                "jobUrl": (
                    "https://jobs.ashbyhq.com/example/job123"
                ),
                "applyUrl": (
                    "https://jobs.ashbyhq.com/example/job123/apply"
                ),
            }
        ]
    }

    source = AshbyJobSource(
        company_name="Example Corp",
        board_name="example",
        opener=lambda request, timeout: FakeResponse(payload),
    )

    jobs = source.fetch_jobs()

    assert len(jobs) == 1

    job = jobs[0]

    assert job.title == "Embedded Hardware Engineer"
    assert job.company == "Example Corp"
    assert job.source == "ashby"
    assert job.source_job_id
    assert str(job.source_url) == (
        "https://jobs.ashbyhq.com/example/job123"
    )
    assert job.location == "Bengaluru, India; Remote"
    assert job.employment_type == "FullTime"

    assert "embedded" in job.skills
    assert "hardware" in job.skills
    assert "pcb" in job.skills
    assert "i2c" in job.skills


def test_ashby_source_skips_unlisted_jobs():
    payload = {
        "jobs": [
            {
                "title": "Private Job",
                "location": "Remote",
                "isListed": False,
                "jobUrl": (
                    "https://jobs.ashbyhq.com/example/private"
                ),
            }
        ]
    }

    source = AshbyJobSource(
        company_name="Example Corp",
        board_name="example",
        opener=lambda request, timeout: FakeResponse(payload),
    )

    assert source.fetch_jobs() == []


def test_ashby_source_skips_jobs_without_title_or_url():
    payload = {
        "jobs": [
            {
                "title": "",
                "jobUrl": "https://example.com/job",
            },
            {
                "title": "Missing URL",
            },
        ]
    }

    source = AshbyJobSource(
        company_name="Example Corp",
        board_name="example",
        opener=lambda request, timeout: FakeResponse(payload),
    )

    assert source.fetch_jobs() == []


def test_ashby_source_job_id_is_deterministic():
    payload = {
        "jobs": [
            {
                "title": "Firmware Engineer",
                "jobUrl": (
                    "https://jobs.ashbyhq.com/example/firmware"
                ),
            }
        ]
    }

    source = AshbyJobSource(
        company_name="Example Corp",
        board_name="example",
        opener=lambda request, timeout: FakeResponse(payload),
    )

    first = source.fetch_jobs()[0]
    second = source.fetch_jobs()[0]

    assert first.source_job_id == second.source_job_id
