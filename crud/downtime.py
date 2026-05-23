from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import Downtime, DowntimeCause


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
