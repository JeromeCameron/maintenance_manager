from datetime import date, time
from typing import Optional, Sequence

from sqlmodel import Session, or_, select

from crud.utility import get_holidays
from schema.models import (
    Downtime,
    DowntimeCause,
    DowntimeFactor,
    DowntimeFactorType,
)
from utils.down_hours import get_production_downtime_hours
from utils.utils import clean_update_payload


def _parse_date(v) -> Optional[date]:
    if v is None:
        return None
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v))


def _parse_time(v) -> Optional[time]:
    if v is None:
        return None
    if isinstance(v, time):
        return v
    return time.fromisoformat(str(v))


def calculate_downtime_hours(session: Session, downtime: Downtime) -> None:
    """Derive ``downtime_hours`` from the event's window, shift/holiday aware.
    Only runs when a start date and time are set. When no end date/time is set
    yet, the window is treated as still open and measured up to now — called
    both at write time (add/update) and by the periodic open-downtime
    recompute (see ``recompute_open_downtimes``) so an ongoing event's total
    keeps advancing without someone re-saving it."""
    if downtime.start_date is None or downtime.start_time is None:
        return
    holidays = {h.holiday_date for h in get_holidays(session)}
    downtime.downtime_hours = get_production_downtime_hours(
        _parse_date(downtime.start_date),
        _parse_time(downtime.start_time),
        holidays,
        _parse_date(downtime.end_date),
        _parse_time(downtime.end_time),
        downtime.shift_asset,
    )


def calculate_factor_delay_hours(
    session: Session, factor: DowntimeFactor
) -> None:
    """Derive ``delay_hours`` from the factor's own window, shift/holiday aware,
    using the parent downtime's ``shift_asset``. Only runs when a start date and
    time are set, so a factor without a window keeps its manually entered hours
    (mirrors ``calculate_downtime_hours``). Called both at write time and by the
    periodic open-downtime recompute (see ``recompute_open_downtimes``)."""
    if factor.start_date is None or factor.start_time is None:
        return
    downtime = (
        session.get(Downtime, factor.downtime_id)
        if factor.downtime_id is not None
        else None
    )
    shift_asset = bool(downtime.shift_asset) if downtime is not None else False
    holidays = {h.holiday_date for h in get_holidays(session)}
    factor.delay_hours = get_production_downtime_hours(
        _parse_date(factor.start_date),
        _parse_time(factor.start_time),
        holidays,
        _parse_date(factor.end_date),
        _parse_time(factor.end_time),
        shift_asset,
    )


# ------------------------------------------------------------------
# Downtime Cause


def get_downtime_causes(session: Session) -> Sequence[DowntimeCause]:
    return session.exec(select(DowntimeCause)).all()


def get_downtime_cause(session: Session, cause_id: int) -> Optional[DowntimeCause]:
    return session.get(DowntimeCause, cause_id)


def add_downtime_cause(session: Session, cause: DowntimeCause) -> DowntimeCause:
    session.add(cause)
    session.commit()
    session.refresh(cause)
    return cause


def update_downtime_cause(
    session: Session, cause_id: int, data: DowntimeCause
) -> Optional[DowntimeCause]:
    db_cause: Optional[DowntimeCause] = session.get(DowntimeCause, cause_id)
    if db_cause is None:
        return None
    for key, value in clean_update_payload(data.model_dump(exclude_unset=True)).items():
        setattr(db_cause, key, value)
    session.add(db_cause)
    session.commit()
    session.refresh(db_cause)
    return db_cause


def delete_downtime_cause(session: Session, cause_id: int) -> bool:
    cause = session.get(DowntimeCause, cause_id)
    if cause is None:
        return False
    session.delete(cause)
    session.commit()
    return True


# ------------------------------------------------------------------
# Downtime


def get_downtimes(session: Session) -> Sequence[Downtime]:
    return session.exec(select(Downtime)).all()


def get_downtimes_by_asset(session: Session, asset_id: str) -> Sequence[Downtime]:
    return session.exec(select(Downtime).where(Downtime.asset_id == asset_id)).all()


def get_downtime(session: Session, downtime_id: int) -> Optional[Downtime]:
    return session.get(Downtime, downtime_id)


def add_downtime(session: Session, downtime: Downtime) -> Downtime:
    calculate_downtime_hours(session, downtime)
    session.add(downtime)
    session.commit()
    session.refresh(downtime)
    return downtime


def update_downtime(
    session: Session, downtime_id: int, data: Downtime
) -> Optional[Downtime]:
    db_downtime: Optional[Downtime] = session.get(Downtime, downtime_id)
    if db_downtime is None:
        return None
    for key, value in clean_update_payload(data.model_dump(exclude_unset=True)).items():
        setattr(db_downtime, key, value)
    calculate_downtime_hours(session, db_downtime)
    session.add(db_downtime)
    session.commit()
    session.refresh(db_downtime)
    return db_downtime


def delete_downtime(session: Session, downtime_id: int) -> bool:
    downtime = session.get(Downtime, downtime_id)
    if downtime is None:
        return False
    session.delete(downtime)
    session.commit()
    return True


# ------------------------------------------------------------------
# Downtime Factor Type (managed lookup list)


def get_downtime_factor_types(session: Session) -> Sequence[DowntimeFactorType]:
    return session.exec(select(DowntimeFactorType)).all()


def get_downtime_factor_type(
    session: Session, factor_type_id: int
) -> Optional[DowntimeFactorType]:
    return session.get(DowntimeFactorType, factor_type_id)


def add_downtime_factor_type(
    session: Session, factor_type: DowntimeFactorType
) -> DowntimeFactorType:
    session.add(factor_type)
    session.commit()
    session.refresh(factor_type)
    return factor_type


def update_downtime_factor_type(
    session: Session, factor_type_id: int, data: DowntimeFactorType
) -> Optional[DowntimeFactorType]:
    db_type: Optional[DowntimeFactorType] = session.get(
        DowntimeFactorType, factor_type_id
    )
    if db_type is None:
        return None
    for key, value in clean_update_payload(data.model_dump(exclude_unset=True)).items():
        setattr(db_type, key, value)
    session.add(db_type)
    session.commit()
    session.refresh(db_type)
    return db_type


def delete_downtime_factor_type(session: Session, factor_type_id: int) -> bool:
    factor_type = session.get(DowntimeFactorType, factor_type_id)
    if factor_type is None:
        return False
    session.delete(factor_type)
    session.commit()
    return True


# ------------------------------------------------------------------
# Downtime Factor (rows against a specific downtime)


def get_downtime_factors(session: Session) -> Sequence[DowntimeFactor]:
    return session.exec(select(DowntimeFactor)).all()


def get_downtime_factors_by_downtime(
    session: Session, downtime_id: int
) -> Sequence[DowntimeFactor]:
    return session.exec(
        select(DowntimeFactor).where(DowntimeFactor.downtime_id == downtime_id)
    ).all()


def get_downtime_factor(
    session: Session, factor_id: int
) -> Optional[DowntimeFactor]:
    return session.get(DowntimeFactor, factor_id)


def add_downtime_factor(
    session: Session, factor: DowntimeFactor
) -> DowntimeFactor:
    calculate_factor_delay_hours(session, factor)
    session.add(factor)
    session.commit()
    session.refresh(factor)
    return factor


def update_downtime_factor(
    session: Session, factor_id: int, data: DowntimeFactor
) -> Optional[DowntimeFactor]:
    db_factor: Optional[DowntimeFactor] = session.get(DowntimeFactor, factor_id)
    if db_factor is None:
        return None
    for key, value in clean_update_payload(data.model_dump(exclude_unset=True)).items():
        setattr(db_factor, key, value)
    calculate_factor_delay_hours(session, db_factor)
    session.add(db_factor)
    session.commit()
    session.refresh(db_factor)
    return db_factor


def delete_downtime_factor(session: Session, factor_id: int) -> bool:
    factor = session.get(DowntimeFactor, factor_id)
    if factor is None:
        return False
    session.delete(factor)
    session.commit()
    return True


# ------------------------------------------------------------------
# Open-downtime recompute (keeps ongoing events current between saves)


def recompute_open_downtimes(session: Session) -> tuple[int, int]:
    """Refresh ``downtime_hours`` / ``delay_hours`` for every downtime and
    factor that's still open (missing an end date or time), so an ongoing
    event's totals stay current without someone re-opening and re-saving it.

    Idempotent — safe to call as often as you like. Returns
    ``(downtimes_updated, factors_updated)``.
    """
    open_downtimes = session.exec(
        select(Downtime).where(
            Downtime.start_date.is_not(None),
            Downtime.start_time.is_not(None),
            or_(Downtime.end_date.is_(None), Downtime.end_time.is_(None)),
        )
    ).all()
    for dt in open_downtimes:
        calculate_downtime_hours(session, dt)
        session.add(dt)

    open_factors = session.exec(
        select(DowntimeFactor).where(
            DowntimeFactor.start_date.is_not(None),
            DowntimeFactor.start_time.is_not(None),
            or_(DowntimeFactor.end_date.is_(None), DowntimeFactor.end_time.is_(None)),
        )
    ).all()
    for f in open_factors:
        calculate_factor_delay_hours(session, f)
        session.add(f)

    if open_downtimes or open_factors:
        session.commit()
    return len(open_downtimes), len(open_factors)


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
