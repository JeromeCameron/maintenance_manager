from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import WorkOrder


def get_work_orders(session: Session) -> Sequence[WorkOrder]:
    statement = select(WorkOrder)
    results = session.exec(statement).all()
    return results


def get_work_order(session: Session, work_order_id: str) -> Optional[WorkOrder]:
    work_order = session.get(WorkOrder, work_order_id)
    return work_order


def add_work_order(session: Session, work_order: WorkOrder) -> WorkOrder:
    session.add(work_order)
    session.commit()
    session.refresh(work_order)
    return work_order


def update_work_order(
    session: Session, work_order_id: str, data: WorkOrder
) -> Optional[WorkOrder]:
    db_work_order: Optional[WorkOrder] = session.get(WorkOrder, work_order_id)

    if db_work_order is None:
        return None

    work_order = data.model_dump(exclude_unset=True)
    for key, value in work_order.items():
        setattr(db_work_order, key, value)

    session.add(db_work_order)
    session.commit()
    session.refresh(db_work_order)
    return db_work_order


def delete_work_order(session: Session, work_order_id: str) -> bool:
    work_order = session.get(WorkOrder, work_order_id)
    if work_order is None:
        return False
    session.delete(work_order)
    session.commit()
    return True


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
