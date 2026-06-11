from calendar import monthrange
from datetime import date


def is_work_day(check_date: date, holidays: set) -> bool:
    return check_date.weekday() <= 4 and check_date not in holidays


def last_day_of_month(d: date) -> date:
    return date(d.year, d.month, monthrange(d.year, d.month)[1])


def get_shift_overlap(start1, end1, start2, end2):
    latest_start = max(start1, start2)
    earliest_end = min(end1, end2)
    delta = (earliest_end - latest_start).total_seconds()
    return max(delta, 0) / 3600
