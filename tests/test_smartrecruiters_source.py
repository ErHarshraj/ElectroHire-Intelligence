import json

from packages.job_sources.career.smartrecruiters import (
    SmartRecruitersJobSource,
)


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_smartrecruiters_source_parses_public_job():
    responses = [
        {
            "limit": 100,
            "offset": 0,
            "totalFound": 1,
            "content": [
                {
                    "id": "123456",
                    "uuid": "posting-uuid",
                }
            ],
        },
        {
            "id": "123456",
            "uuid": "posting-uuid",
            "name": "Embedded Hardware Engineer",
            "releasedDate": "2026-09-10T10:00:00.000Z",
            "postingUrl": (
                "https://jobs.smartrecruiters.com/"
                "ExampleCorp/123456-embedded-hardware-engineer"
            ),
            "applyUrl": (
                "https://jobs.smartrecruiters.com/"
                "ExampleCorp/123456-embedded-hardware-engineer"
            ),
            "location": {
                "city": "Bengaluru",
                "region": "Karnataka",
                "country": "in",
                "remote": True,
            },
            "typeOfEmployment": {
                "label": "Full-time",
            },
            "experienceLevel": {
                "label": "Entry Level",
            },
            "jobAd": {
                "sections": {
                    "companyDescription": {
                        "title": "Company Description",
                        "text": "Example company.",
                    },
                    "jobDescription": {
                        "title": "Job Description",
                        "text": (
                            "Design embedded hardware and "
                            "microcontroller systems."
                        ),
                    },
                    "qualifications": {
                        "title": "Qualifications",
                        "text": "PCB and electronics experience.",
                    },
                }
            },
            "active": True,
        },
    ]

    calls = []

    def fake_opener(request, timeout):
        calls.append(request.full_url)
        return FakeResponse(responses.pop(0))

    source = SmartRecruitersJobSource(
        company_name="Example Corp",
        company_identifier="examplecorp",
        opener=fake_opener,
    )

    jobs = source.fetch_jobs()

    assert len(jobs) == 1

    job = jobs[0]

    assert job.title == "Embedded Hardware Engineer"
    assert job.company == "Example Corp"
    assert job.source == "smartrecruiters"
    assert job.source_job_id == "posting-uuid"
    assert "Bengaluru" in job.location
    assert "Remote" in job.location
    assert job.employment_type == "Full-time"
    assert job.experience_required == "Entry Level"
    assert "embedded" in job.skills
    assert "hardware" in job.skills
    assert "microcontroller" in job.skills
    assert "pcb" in job.skills
    assert job.description is not None
    assert "Design embedded hardware" in job.description

    assert len(calls) == 2


def test_smartrecruiters_source_skips_inactive_job():
    responses = [
        {
            "limit": 100,
            "offset": 0,
            "totalFound": 1,
            "content": [
                {
                    "id": "123456",
                }
            ],
        },
        {
            "id": "123456",
            "name": "Inactive Job",
            "active": False,
            "postingUrl": (
                "https://jobs.smartrecruiters.com/"
                "ExampleCorp/123456-inactive-job"
            ),
        },
    ]

    def fake_opener(request, timeout):
        return FakeResponse(responses.pop(0))

    source = SmartRecruitersJobSource(
        company_name="Example Corp",
        company_identifier="examplecorp",
        opener=fake_opener,
    )

    assert source.fetch_jobs() == []


def test_smartrecruiters_source_handles_pagination():
    responses = [
        {
            "limit": 100,
            "offset": 0,
            "totalFound": 2,
            "content": [
                {"id": "1"},
            ],
        },
        {
            "limit": 100,
            "offset": 100,
            "totalFound": 2,
            "content": [
                {"id": "2"},
            ],
        },
        {
            "id": "1",
            "uuid": "uuid-1",
            "name": "Job One",
            "postingUrl": "https://example.com/job-one",
            "active": True,
        },
        {
            "id": "2",
            "uuid": "uuid-2",
            "name": "Job Two",
            "postingUrl": "https://example.com/job-two",
            "active": True,
        },
    ]

    calls = []

    def fake_opener(request, timeout):
        calls.append(request.full_url)
        return FakeResponse(responses.pop(0))

    source = SmartRecruitersJobSource(
        company_name="Example Corp",
        company_identifier="examplecorp",
        opener=fake_opener,
    )

    jobs = source.fetch_jobs()

    assert len(jobs) == 2
    assert jobs[0].title == "Job One"
    assert jobs[1].title == "Job Two"

    assert "offset=0" in calls[0]
    assert "offset=100" in calls[1]
