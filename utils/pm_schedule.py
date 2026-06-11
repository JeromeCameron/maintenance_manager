from calendar import monthrange
from datetime import date, timedelta

from schema.models import PmFrequency


def _add_months(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, monthrange(year, month)[1])
    return date(year, month, day)


def next_service_date(last_service_date: date, frequency: PmFrequency) -> date:
    match frequency:
        case PmFrequency.daily:
            return last_service_date + timedelta(days=1)
        case PmFrequency.weekly:
            return last_service_date + timedelta(weeks=1)
        case PmFrequency.fortnightly:
            return last_service_date + timedelta(weeks=2)
        case PmFrequency.monthly:
            return _add_months(last_service_date, 1)
        case PmFrequency.every_other_month:
            return _add_months(last_service_date, 2)
        case PmFrequency.every_four_month:
            return _add_months(last_service_date, 4)
        case PmFrequency.quarterly:
            return _add_months(last_service_date, 3)
        case PmFrequency.biannually:
            return _add_months(last_service_date, 6)
        case PmFrequency.annually:
            return _add_months(last_service_date, 12)
