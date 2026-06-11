from datetime import date, datetime, time, timedelta

from sqlmodel import Session

from crud.utility import get_holidays
from utils.utils import get_shift_overlap, is_work_day


def get_production_hours(
    session: Session,
    start_date: date,
    start_time: time,
    end_date: date | None = None,
    end_time: time | None = None,
    shift_depot: bool = False,
) -> float:
    holidays = {h.holiday_date for h in get_holidays(session)}

    effective_start = datetime.combine(start_date, start_time)
    effective_end = datetime.combine(end_date, end_time) if end_date and end_time else datetime.now()

    total_hours = 0.0
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

            # Night shift: 22:00 to 06:00 next day (second shift)
            if shift_depot:
                total_hours += get_shift_overlap(
                    datetime.combine(curr_date, time(22, 0)),
                    datetime.combine(curr_date + timedelta(days=1), time(6, 0)),
                    effective_start,
                    effective_end,
                )

        curr_date += timedelta(days=1)

    return round(total_hours, 2)
