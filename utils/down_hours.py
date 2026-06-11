from datetime import date, datetime, time, timedelta

from sqlmodel import Session

from crud.utility import get_holidays
from utils.utils import get_shift_overlap, is_work_day, last_day_of_month


def get_production_downtime_hours(
    session: Session,
    start_date: date,
    start_time: time,
    end_date: date | None = None,
    end_time: time | None = None,
    shift_asset: bool = False,
) -> float:
    holidays = {h.holiday_date for h in get_holidays(session)}

    effective_start = datetime.combine(start_date, start_time)
    effective_end = datetime.combine(end_date, end_time) if end_date and end_time else datetime.now()

    total_hours = 0.0
    # Start one day before to capture night shifts that began the prior evening
    curr_date = effective_start.date() - timedelta(days=1)

    while curr_date <= effective_end.date():
        if is_work_day(curr_date, holidays):
            # Day shift: 08:00–16:00
            total_hours += get_shift_overlap(
                datetime.combine(curr_date, time(8, 0)),
                datetime.combine(curr_date, time(16, 0)),
                effective_start,
                effective_end,
            )

            # Night shift: 22:00 to 06:00 next day as a single block
            if shift_asset:
                total_hours += get_shift_overlap(
                    datetime.combine(curr_date, time(22, 0)),
                    datetime.combine(curr_date + timedelta(days=1), time(6, 0)),
                    effective_start,
                    effective_end,
                )

        curr_date += timedelta(days=1)

    return round(total_hours, 2)


def split_downtime_by_month(
    session: Session,
    start_date: date,
    start_time: time,
    end_date: date | None = None,
    end_time: time | None = None,
    shift_asset: bool = False,
) -> list[dict]:
    if end_date is None or end_time is None:
        effective_end_date = date.today()
        effective_end_time = datetime.now().time()
    else:
        effective_end_date = end_date
        effective_end_time = end_time

    month_count = (
        (effective_end_date.year - start_date.year) * 12
        + effective_end_date.month - start_date.month + 1
    )

    if month_count <= 0:
        return []

    results = []
    month_start = date(start_date.year, start_date.month, 1)

    for i in range(1, month_count + 1):
        month_last = last_day_of_month(month_start)

        seg_start_date = start_date if i == 1 else month_start
        seg_start_time = start_time if i == 1 else time(0, 0, 0)

        # For mid-range months, end at 06:00 on the first day of the next month
        # so the night shift spanning the month boundary is fully captured
        seg_end_date = effective_end_date if i == month_count else month_last + timedelta(days=1)
        seg_end_time = effective_end_time if i == month_count else time(6, 0, 0)

        results.append({
            "month": month_start.strftime("%B %Y"),
            "hours": get_production_downtime_hours(
                session,
                seg_start_date, seg_start_time,
                seg_end_date, seg_end_time,
                shift_asset,
            ),
        })

        month_start = month_last + timedelta(days=1)

    return results
