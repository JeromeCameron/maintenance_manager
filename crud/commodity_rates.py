from datetime import date
from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import CommodityRate


def get_rates(session: Session) -> Sequence[CommodityRate]:
    return session.exec(select(CommodityRate).order_by(CommodityRate.effective_date.desc())).all()  # type: ignore[attr-defined]


def get_rate(session: Session, rate_id: int) -> Optional[CommodityRate]:
    return session.get(CommodityRate, rate_id)


def get_rate_at(session: Session, on_date: date) -> Optional[CommodityRate]:
    """Return the rate in effect on a given date (highest effective_date <= on_date)."""
    return session.exec(
        select(CommodityRate)
        .where(CommodityRate.effective_date <= on_date)
        .order_by(CommodityRate.effective_date.desc())  # type: ignore[attr-defined]
    ).first()


def add_rate(session: Session, rate: CommodityRate) -> CommodityRate:
    session.add(rate)
    session.commit()
    session.refresh(rate)
    return rate


def update_rate(session: Session, rate_id: int, data: CommodityRate) -> Optional[CommodityRate]:
    rec = session.get(CommodityRate, rate_id)
    if rec is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(rec, key, value)
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec


def delete_rate(session: Session, rate_id: int) -> bool:
    rec = session.get(CommodityRate, rate_id)
    if rec is None:
        return False
    session.delete(rec)
    session.commit()
    return True
