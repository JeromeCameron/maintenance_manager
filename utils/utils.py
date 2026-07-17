from calendar import monthrange
from datetime import date, datetime
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo("America/Jamaica")


def now_local() -> datetime:
    """Current datetime in Jamaica time, naive (tzinfo stripped for compatibility)."""
    return datetime.now(APP_TZ).replace(tzinfo=None)


def today_local() -> date:
    """Current date in Jamaica time."""
    return datetime.now(APP_TZ).date()


def is_work_day(check_date: date, holidays: set) -> bool:
    return check_date.weekday() <= 4 and check_date not in holidays


def last_day_of_month(d: date) -> date:
    return date(d.year, d.month, monthrange(d.year, d.month)[1])


def get_shift_overlap(start1, end1, start2, end2):
    latest_start = max(start1, start2)
    earliest_end = min(end1, end2)
    delta = (earliest_end - latest_start).total_seconds()
    return max(delta, 0) / 3600


def clean_update_payload(data: dict) -> dict:
    """Treat '' as "clear this field" so optional date/numeric columns don't get sent
    an empty string on update (e.g. a cleared HTML date input), which the DB rejects."""
    return {k: (None if v == "" else v) for k, v in data.items()}
