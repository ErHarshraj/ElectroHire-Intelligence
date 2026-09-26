from datetime import datetime, timezone

import pytest

from packages.application.career_application_service import (
    CareerApplicationService,
)
from packages.application.career_models import (
    CareerApplicationRecord,
    CareerApplicationStatus,
    InvalidCareerApplicationTransition,
)
from packages.persistence.career_application_repository import (
    CareerApplicationRepository,
)


class FakeCareerApplicationRepository(CareerApplicationRepository):
    def __init__(self) -> None:
        self.records: dict[int, CareerApplicationRecord] = {}
        self.next_id = 1

    def save(self, record: CareerApplicationRecord) -> int:
        application_id = self.next_id
        self.next_id += 1

        self.records[application_id] = CareerApplicationRecord(
            job_id=record.job_id,
            status=record.status,
            id=application_id,
            application_url=record.application_url,
            applied_at=record.applied_at,
            notes=record.notes,
            last_followup_at=record.last_followup_at,
            next_followup_at=record.next_followup_at,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

        return application_id

    def get(self, application_id: int) -> CareerApplicationRecord | None:
        return self.records.get(application_id)

    def get_by_job(self, job_id: int) -> CareerApplicationRecord | None:
        return next(
            (
                record
                for record in self.records.values()
                if record.job_id == job_id
            ),
            None,
        )

    def list_by_status(
        self,
        status: CareerApplicationStatus,
    ) -> list[CareerApplicationRecord]:
        return [
            record
            for record in self.records.values()
            if record.status == status
        ]

    def update(
        self,
        application_id: int,
        *,
        status: CareerApplicationStatus,
        application_url: str | None = None,
        applied_at: datetime | None = None,
        notes: str = "",
        last_followup_at: datetime | None = None,
        next_followup_at: datetime | None = None,
    ) -> None:
        record = self.records[application_id]

        self.records[application_id] = CareerApplicationRecord(
            job_id=record.job_id,
            status=status,
            id=record.id,
            application_url=application_url,
            applied_at=applied_at,
            notes=notes,
            last_followup_at=last_followup_at,
            next_followup_at=next_followup_at,
            created_at=record.created_at,
            updated_at=datetime.now(timezone.utc),
        )


def make_service() -> CareerApplicationService:
    return CareerApplicationService(
        FakeCareerApplicationRepository()
    )


def test_create_application() -> None:
    service = make_service()

    application_id = service.create(job_id=101)

    record = service.get(application_id)

    assert record is not None
    assert record.job_id == 101
    assert record.status == CareerApplicationStatus.SHORTLISTED
    assert record.created_at is not None
    assert record.updated_at is not None


def test_create_rejects_duplicate_job() -> None:
    service = make_service()

    service.create(job_id=101)

    with pytest.raises(ValueError, match="already exists"):
        service.create(job_id=101)


def test_get_by_job() -> None:
    service = make_service()

    application_id = service.create(job_id=101)

    record = service.get_by_job(101)

    assert record is not None
    assert record.id == application_id


def test_valid_transition() -> None:
    service = make_service()

    application_id = service.create(job_id=101)

    service.transition(
        application_id,
        CareerApplicationStatus.APPLIED,
    )

    record = service.get(application_id)

    assert record is not None
    assert record.status == CareerApplicationStatus.APPLIED


def test_invalid_transition_is_rejected() -> None:
    service = make_service()

    application_id = service.create(job_id=101)

    with pytest.raises(InvalidCareerApplicationTransition):
        service.transition(
            application_id,
            CareerApplicationStatus.INTERVIEW,
        )


def test_transition_missing_application() -> None:
    service = make_service()

    with pytest.raises(ValueError, match="does not exist"):
        service.transition(
            999,
            CareerApplicationStatus.APPLIED,
        )


def test_update_tracking() -> None:
    service = make_service()

    application_id = service.create(job_id=101)

    applied_at = datetime.now(timezone.utc)

    service.update_tracking(
        application_id,
        application_url="https://example.com/apply",
        applied_at=applied_at,
        notes="Submitted through company portal",
        next_followup_at=applied_at,
    )

    record = service.get(application_id)

    assert record is not None
    assert record.status == CareerApplicationStatus.SHORTLISTED
    assert record.application_url == "https://example.com/apply"
    assert record.applied_at == applied_at
    assert record.notes == "Submitted through company portal"
    assert record.next_followup_at == applied_at


def test_update_tracking_missing_application() -> None:
    service = make_service()

    with pytest.raises(ValueError, match="does not exist"):
        service.update_tracking(999, notes="missing")


def test_list_by_status() -> None:
    service = make_service()

    first_id = service.create(job_id=101)
    second_id = service.create(job_id=102)

    service.transition(
        first_id,
        CareerApplicationStatus.APPLIED,
    )

    applied = service.list_by_status(
        CareerApplicationStatus.APPLIED,
    )

    assert [record.id for record in applied] == [first_id]

    shortlisted = service.list_by_status(
        CareerApplicationStatus.SHORTLISTED,
    )

    assert [record.id for record in shortlisted] == [second_id]
