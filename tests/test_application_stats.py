from packages.application.models import ApplicationStatus
from packages.application.stats import ApplicationRunStats


def test_application_stats_starts_at_zero() -> None:
    stats = ApplicationRunStats()

    assert stats.apply_decisions == 0
    assert stats.targets_found == 0
    assert stats.no_target == 0
    assert stats.submitted == 0
    assert stats.pending == 0
    assert stats.failed == 0
    assert stats.paused == 0
    assert stats.already_submitted == 0


def test_application_stats_records_targets() -> None:
    stats = ApplicationRunStats()

    stats.record_target_found()
    stats.record_target_found()
    stats.record_no_target()

    assert stats.targets_found == 2
    assert stats.no_target == 1


def test_application_stats_records_application_results() -> None:
    stats = ApplicationRunStats()

    stats.record_result(ApplicationStatus.SUBMITTED)
    stats.record_result(ApplicationStatus.PENDING)
    stats.record_result(ApplicationStatus.FAILED)
    stats.record_result(ApplicationStatus.PAUSED)
    stats.record_result(ApplicationStatus.ALREADY_SUBMITTED)

    assert stats.submitted == 1
    assert stats.pending == 1
    assert stats.failed == 1
    assert stats.paused == 1
    assert stats.already_submitted == 1
