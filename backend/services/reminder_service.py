from datetime import UTC, datetime, time, timedelta
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


TIME_PATTERN = re.compile(r"^(\d{1,2}):(\d{2})\s*(AM|PM)$", re.IGNORECASE)
ALLOWED_NOTIFICATION_PREFERENCES = {"in_app", "browser", "email"}


def validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("timezone must be an IANA timezone, such as Asia/Tokyo.") from exc
    return value


def parse_local_time(value: str) -> time:
    match = TIME_PATTERN.fullmatch(value.strip())
    if not match:
        raise ValueError("reminder_time must use HH:MM AM/PM format.")
    hour, minute, period = int(match.group(1)), int(match.group(2)), match.group(3).upper()
    if not 1 <= hour <= 12 or not 0 <= minute <= 59:
        raise ValueError("reminder_time contains an invalid hour or minute.")
    hour = hour % 12 + (12 if period == "PM" else 0)
    return time(hour, minute)


def normalize_notification_preferences(value: str) -> str:
    preferences = [item.strip() for item in value.split(",") if item.strip()]
    if not preferences or any(item not in ALLOWED_NOTIFICATION_PREFERENCES for item in preferences):
        raise ValueError("notification_pref must contain one or more of: in_app, browser, email.")
    return ",".join(dict.fromkeys(preferences))


def first_occurrence(reminder_time: str, timezone_name: str, now: datetime | None = None) -> datetime:
    zone = ZoneInfo(validate_timezone(timezone_name))
    local_now = (now or datetime.now(UTC)).astimezone(zone)
    candidate = datetime.combine(local_now.date(), parse_local_time(reminder_time), tzinfo=zone)
    if candidate <= local_now:
        candidate += timedelta(days=1)
    return candidate.astimezone(UTC)


def next_occurrence(scheduled_for: datetime, frequency: str, timezone_name: str) -> datetime | None:
    if frequency == "once":
        return None
    if frequency == "every_8_hours":
        return scheduled_for.astimezone(UTC) + timedelta(hours=8)
    zone = ZoneInfo(validate_timezone(timezone_name))
    local_scheduled = scheduled_for.astimezone(zone)
    days = 1 if frequency == "daily" else 7
    return (local_scheduled + timedelta(days=days)).astimezone(UTC)


def retry_at(attempt_count: int, now: datetime | None = None) -> datetime:
    # 1, 2, 4, 8, 16 minute exponential backoff, capped at one hour.
    minutes = min(2 ** max(attempt_count - 1, 0), 60)
    return (now or datetime.now(UTC)) + timedelta(minutes=minutes)
