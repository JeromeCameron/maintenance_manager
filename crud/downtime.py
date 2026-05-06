from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import Downtime


def get_downtimes(session: Session) -> Sequence[Downtime]:
    statement = select(Downtime)
    results = session.exec(statement).all()
    return results


def get_downtime(session: Session, downtime_id: str) -> Optional[Downtime]:
    downtime = session.get(Downtime, downtime_id)
    return downtime


def add_downtime(session: Session, downtime: Downtime) -> Downtime:
    session.add(downtime)
    session.commit()
    session.refresh(downtime)
    return downtime


def update_downtime(
    session: Session, downtime_id: str, data: Downtime
) -> Optional[Downtime]:
    db_downtime: Optional[Downtime] = session.get(Downtime, downtime_id)

    if db_downtime is None:
        return None

    downtime = data.model_dump(exclude_unset=True)
    for key, value in downtime.items():
        setattr(db_downtime, key, value)

    session.add(db_downtime)
    session.commit()
    session.refresh(db_downtime)
    return db_downtime


def delete_downtime(session: Session, downtime_id: str) -> bool:
    downtime = session.get(Downtime, downtime_id)
    if downtime is None:
        return False
    session.delete(downtime)
    session.commit()
    return True


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
