from datetime import date, time
from typing import Optional, Sequence

from sqlmodel import Session, select

from crud.utility import get_holidays
from schema.models import Downtime, DowntimeCause
from utils.down_hours import get_production_downtime_hours


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


def _calculate_downtime_hours(session: Session, downtime: Downtime) -> None:
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
    for key, value in data.model_dump(exclude_unset=True).items():
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
    _calculate_downtime_hours(session, downtime)
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
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_downtime, key, value)
    _calculate_downtime_hours(session, db_downtime)
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


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
