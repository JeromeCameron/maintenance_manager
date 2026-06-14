from datetime import date
from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import AssetPM, PmPlans
from utils.pm_schedule import next_service_date


def _recalc_next_service(session: Session, apm: AssetPM) -> None:
    """Set next_service from last_service + plan frequency if both are available."""
    if apm.last_service and apm.pm_plan_id:
        plan = session.get(PmPlans, apm.pm_plan_id)
        if plan and plan.frequency:
            last_service = apm.last_service
            if isinstance(last_service, str):
                last_service = date.fromisoformat(last_service)
            apm.next_service = next_service_date(last_service, plan.frequency)


# ------------------------------------------------------------------
# PM Plans


def get_pm_plans(session: Session) -> Sequence[PmPlans]:
    return session.exec(select(PmPlans)).all()


def get_pm_plan(session: Session, pm_id: str) -> Optional[PmPlans]:
    return session.get(PmPlans, pm_id)


def add_pm_plan(session: Session, pm_plan: PmPlans) -> PmPlans:
    session.add(pm_plan)
    session.commit()
    session.refresh(pm_plan)
    return pm_plan


def update_pm_plan(session: Session, pm_id: str, data: PmPlans) -> Optional[PmPlans]:
    db_pm: Optional[PmPlans] = session.get(PmPlans, pm_id)
    if db_pm is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_pm, key, value)
    session.add(db_pm)
    session.commit()
    session.refresh(db_pm)
    return db_pm


def delete_pm_plan(session: Session, pm_id: str) -> bool:
    pm = session.get(PmPlans, pm_id)
    if pm is None:
        return False
    session.delete(pm)
    session.commit()
    return True


# ------------------------------------------------------------------
# Asset PM


def get_asset_pms(session: Session) -> Sequence[AssetPM]:
    return session.exec(select(AssetPM)).all()


def get_asset_pms_by_asset(session: Session, asset_id: str) -> Sequence[AssetPM]:
    return session.exec(select(AssetPM).where(AssetPM.asset_id == asset_id)).all()


def get_asset_pm(session: Session, asset_pm_id: int) -> Optional[AssetPM]:
    return session.get(AssetPM, asset_pm_id)


def add_asset_pm(session: Session, asset_pm: AssetPM) -> AssetPM:
    _recalc_next_service(session, asset_pm)
    session.add(asset_pm)
    session.commit()
    session.refresh(asset_pm)
    return asset_pm


def update_asset_pm(session: Session, asset_pm_id: int, data: AssetPM) -> Optional[AssetPM]:
    db_apm: Optional[AssetPM] = session.get(AssetPM, asset_pm_id)
    if db_apm is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_apm, key, value)
    _recalc_next_service(session, db_apm)
    session.add(db_apm)
    session.commit()
    session.refresh(db_apm)
    return db_apm


def delete_asset_pm(session: Session, asset_pm_id: int) -> bool:
    apm = session.get(AssetPM, asset_pm_id)
    if apm is None:
        return False
    session.delete(apm)
    session.commit()
    return True


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
