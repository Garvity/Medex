from datetime import UTC, datetime

import pytest

from services.reminder_service import (
    first_occurrence,
    next_occurrence,
    normalize_notification_preferences,
    parse_local_time,
    retry_at,
    validate_timezone,
)
from schemas import ReminderCreateRequest


def test_first_occurrence_converts_tokyo_local_time_to_UTC() -> None:
    occurrence = first_occurrence(
        "09:30 AM", "Asia/Tokyo", now=datetime(2026, 7, 30, 0, 0, tzinfo=UTC)
    )
    assert occurrence == datetime(2026, 7, 30, 0, 30, tzinfo=UTC)


@pytest.mark.parametrize("value", ["25:00 PM", "08:61 AM", "8am", "14:00"])
def test_parse_local_time_rejects_non_normalized_time(value: str) -> None:
    with pytest.raises(ValueError):
        parse_local_time(value)


def test_validate_timezone_rejects_unknown_zone() -> None:
    with pytest.raises(ValueError):
        validate_timezone("Mars/Olympus")


def test_notification_preferences_are_normalized_and_validated() -> None:
    assert normalize_notification_preferences(" email, in_app, email ") == "email,in_app"
    with pytest.raises(ValueError):
        normalize_notification_preferences("email,sms")


def test_reminder_request_defaults_to_india_timezone() -> None:
    request = ReminderCreateRequest(medicine="Aspirin", reminder_time="08:00 AM")
    assert request.timezone == "Asia/Kolkata"


def test_daily_and_weekly_occurrences_preserve_local_wall_time() -> None:
    # The day before the US DST transition: 09:00 remains 09:00 local after it.
    scheduled_for = datetime(2026, 3, 7, 14, 0, tzinfo=UTC)
    daily = next_occurrence(scheduled_for, "daily", "America/New_York")
    weekly = next_occurrence(scheduled_for, "weekly", "America/New_York")
    assert daily == datetime(2026, 3, 8, 13, 0, tzinfo=UTC)
    assert weekly == datetime(2026, 3, 14, 13, 0, tzinfo=UTC)


def test_every_eight_hours_uses_elapsed_UTC_time() -> None:
    scheduled_for = datetime(2026, 7, 30, 1, 0, tzinfo=UTC)
    assert next_occurrence(scheduled_for, "every_8_hours", "Asia/Tokyo") == datetime(
        2026, 7, 30, 9, 0, tzinfo=UTC
    )


def test_retry_backoff_is_exponential_and_capped() -> None:
    now = datetime(2026, 7, 30, 0, 0, tzinfo=UTC)
    assert retry_at(1, now) == datetime(2026, 7, 30, 0, 1, tzinfo=UTC)
    assert retry_at(5, now) == datetime(2026, 7, 30, 0, 16, tzinfo=UTC)
    assert retry_at(10, now) == datetime(2026, 7, 30, 1, 0, tzinfo=UTC)
