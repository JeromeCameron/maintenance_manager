from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import WorkOrder, WorkOrderPart


# ------------------------------------------------------------------
# Work Order


def get_work_orders(session: Session) -> Sequence[WorkOrder]:
    return session.exec(select(WorkOrder)).all()


def get_work_orders_by_asset(session: Session, asset_id: str) -> Sequence[WorkOrder]:
    return session.exec(select(WorkOrder).where(WorkOrder.asset_id == asset_id)).all()


def get_work_order(session: Session, work_order_id: int) -> Optional[WorkOrder]:
    return session.get(WorkOrder, work_order_id)


def add_work_order(session: Session, work_order: WorkOrder) -> WorkOrder:
    session.add(work_order)
    session.commit()
    session.refresh(work_order)
    return work_order


def update_work_order(
    session: Session, work_order_id: int, data: WorkOrder
) -> Optional[WorkOrder]:
    db_work_order: Optional[WorkOrder] = session.get(WorkOrder, work_order_id)
    if db_work_order is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_work_order, key, value)
    session.add(db_work_order)
    session.commit()
    session.refresh(db_work_order)
    return db_work_order


def delete_work_order(session: Session, work_order_id: int) -> bool:
    work_order = session.get(WorkOrder, work_order_id)
    if work_order is None:
        return False
    session.delete(work_order)
    session.commit()
    return True


# ------------------------------------------------------------------
# Work Order Part


def get_work_order_parts(session: Session) -> Sequence[WorkOrderPart]:
    return session.exec(select(WorkOrderPart)).all()


def get_work_order_parts_by_work_order(session: Session, work_order_id: int) -> Sequence[WorkOrderPart]:
    return session.exec(select(WorkOrderPart).where(WorkOrderPart.work_order_id == work_order_id)).all()


def get_work_order_part(session: Session, work_order_part_id: int) -> Optional[WorkOrderPart]:
    return session.get(WorkOrderPart, work_order_part_id)


def add_work_order_part(session: Session, work_order_part: WorkOrderPart) -> WorkOrderPart:
    session.add(work_order_part)
    session.commit()
    session.refresh(work_order_part)
    return work_order_part


def update_work_order_part(
    session: Session, work_order_part_id: int, data: WorkOrderPart
) -> Optional[WorkOrderPart]:
    db_wop: Optional[WorkOrderPart] = session.get(WorkOrderPart, work_order_part_id)
    if db_wop is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_wop, key, value)
    session.add(db_wop)
    session.commit()
    session.refresh(db_wop)
    return db_wop


def delete_work_order_part(session: Session, work_order_part_id: int) -> bool:
    wop = session.get(WorkOrderPart, work_order_part_id)
    if wop is None:
        return False
    session.delete(wop)
    session.commit()
    return True


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
