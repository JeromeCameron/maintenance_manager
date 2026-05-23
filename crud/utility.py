from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import Holidays


def get_holidays(session: Session) -> Sequence[Holidays]:
    return session.exec(select(Holidays)).all()


def get_holiday(session: Session, holiday_id: int) -> Optional[Holidays]:
    return session.get(Holidays, holiday_id)


def add_holiday(session: Session, holiday: Holidays) -> Holidays:
    session.add(holiday)
    session.commit()
    session.refresh(holiday)
    return holiday


def update_holiday(session: Session, holiday_id: int, data: Holidays) -> Optional[Holidays]:
    db_holiday: Optional[Holidays] = session.get(Holidays, holiday_id)
    if db_holiday is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_holiday, key, value)
    session.add(db_holiday)
    session.commit()
    session.refresh(db_holiday)
    return db_holiday


def delete_holiday(session: Session, holiday_id: int) -> bool:
    holiday = session.get(Holidays, holiday_id)
    if holiday is None:
        return False
    session.delete(holiday)
    session.commit()
    return True


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
