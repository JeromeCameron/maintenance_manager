from collections.abc import Iterator
from datetime import date, datetime, time, timedelta

from sqlmodel import Session

from crud.utility import get_holidays
from utils.utils import get_shift_overlap, is_work_day, now_local


def _iter_shift_overlaps(
    effective_start: datetime,
    effective_end: datetime,
    holidays: set[date],
    shift_asset: bool,
) -> Iterator[tuple[date, float]]:
    """Yield ``(day, hours)`` for every work-day shift block that overlaps
    ``[effective_start, effective_end]``.

    Each work day contributes its day shift (08:00–16:00) and, for shift assets,
    its night shift (22:00 → 06:00 the next day) as a single block. The night
    shift is attributed to the calendar day it *starts* on, so a block is never
    counted twice and never split across two months.
    """
    # Start one day before to capture a night shift that began the prior evening.
    curr_date = effective_start.date() - timedelta(days=1)
    while curr_date <= effective_end.date():
        if is_work_day(curr_date, holidays):
            yield curr_date, get_shift_overlap(
                datetime.combine(curr_date, time(8, 0)),
                datetime.combine(curr_date, time(16, 0)),
                effective_start,
                effective_end,
            )
            if shift_asset:
                yield curr_date, get_shift_overlap(
                    datetime.combine(curr_date, time(22, 0)),
                    datetime.combine(curr_date + timedelta(days=1), time(6, 0)),
                    effective_start,
                    effective_end,
                )
        curr_date += timedelta(days=1)


def get_production_downtime_hours(
    start_date: date,
    start_time: time,
    holidays: set[date],
    end_date: date | None = None,
    end_time: time | None = None,
    shift_asset: bool = False,
) -> float:
    effective_start = datetime.combine(start_date, start_time)
    effective_end = datetime.combine(end_date, end_time) if end_date and end_time else now_local()

    total_hours = sum(
        hours for _, hours in _iter_shift_overlaps(effective_start, effective_end, holidays, shift_asset)
    )
    return round(total_hours, 2)


def split_downtime_by_month(
    session: Session,
    start_date: date,
    start_time: time,
    end_date: date | None = None,
    end_time: time | None = None,
    shift_asset: bool = False,
    holidays: set[date] | None = None,
) -> list[dict]:
    """Split an event's production downtime hours across the calendar months it
    spans. ``sum(seg["hours"] for seg in ...)`` equals
    ``get_production_downtime_hours`` for the whole event (both walk the same
    shift blocks; the split just buckets each block by the month of the day it
    starts on)."""
    if holidays is None:
        holidays = {h.holiday_date for h in get_holidays(session)}

    effective_start = datetime.combine(start_date, start_time)
    if end_date is None or end_time is None:
        effective_end = now_local()
    else:
        effective_end = datetime.combine(end_date, end_time)

    if effective_end <= effective_start:
        return []

    buckets: dict[tuple[int, int], float] = {}
    for day, hours in _iter_shift_overlaps(effective_start, effective_end, holidays, shift_asset):
        if hours <= 0:
            continue
        key = (day.year, day.month)
        buckets[key] = buckets.get(key, 0.0) + hours

    return [
        {"month": date(y, m, 1).strftime("%B %Y"), "hours": round(hrs, 2)}
        for (y, m), hrs in sorted(buckets.items())
    ]
