from typing import Optional, Sequence

from sqlalchemy import func
from sqlmodel import Session, select

from schema.models import ReactivityStats, ReactivityTrendMonth, WorkOrder, WorkOrderPart


def _next_work_order_id(session: Session) -> int:
    max_id = session.exec(select(func.max(WorkOrder.work_order_id))).first()
    return max(max_id or 0, 999) + 1


# ------------------------------------------------------------------
# Work Order


def get_reactivity_stats(session: Session) -> ReactivityStats:
    total = session.exec(select(func.count(WorkOrder.work_order_id))).first() or 0
    planned = session.exec(
        select(func.count(WorkOrder.work_order_id)).where(WorkOrder.planned == True)  # noqa: E712
    ).first() or 0
    unplanned = total - planned
    return ReactivityStats(
        total=total,
        planned=planned,
        unplanned=unplanned,
        planned_pct=round((planned / total * 100), 1) if total else 0,
        unplanned_pct=round((unplanned / total * 100), 1) if total else 0,
    )


def get_reactivity_trend(session: Session, months: int = 6) -> list[ReactivityTrendMonth]:
    from datetime import date as date_type

    today = date_type.today()
    month_list: list[tuple[int, int]] = []
    for i in range(months - 1, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        month_list.append((y, m))

    start_date = date_type(month_list[0][0], month_list[0][1], 1)

    all_wos = session.exec(
        select(WorkOrder)
        .where(WorkOrder.issue_date.is_not(None))  # type: ignore[union-attr]
        .where(WorkOrder.issue_date >= start_date)
    ).all()

    planned_counts: dict[tuple[int, int], int] = {k: 0 for k in month_list}
    unplanned_counts: dict[tuple[int, int], int] = {k: 0 for k in month_list}

    for wo in all_wos:
        if wo.issue_date is None:
            continue
        key = (wo.issue_date.year, wo.issue_date.month)
        if key not in planned_counts:
            continue
        if wo.planned:
            planned_counts[key] += 1
        else:
            unplanned_counts[key] += 1

    result = []
    for (y, m) in month_list:
        planned = planned_counts[(y, m)]
        unplanned = unplanned_counts[(y, m)]
        total = planned + unplanned
        result.append(ReactivityTrendMonth(
            month=f"{y:04d}-{m:02d}",
            planned=planned,
            unplanned=unplanned,
            total=total,
            planned_pct=round(planned / total * 100, 1) if total else 0,
            unplanned_pct=round(unplanned / total * 100, 1) if total else 0,
        ))
    return result


def get_work_orders(session: Session) -> Sequence[WorkOrder]:
    return session.exec(select(WorkOrder)).all()


def get_work_orders_by_asset(session: Session, asset_id: str) -> Sequence[WorkOrder]:
    return session.exec(select(WorkOrder).where(WorkOrder.asset_id == asset_id)).all()


def get_work_orders_by_supplier(session: Session, supplier_id: int) -> Sequence[WorkOrder]:
    return session.exec(select(WorkOrder).where(WorkOrder.supplier_id == supplier_id)).all()


def get_work_order(session: Session, work_order_id: int) -> Optional[WorkOrder]:
    return session.get(WorkOrder, work_order_id)


def add_work_order(session: Session, work_order: WorkOrder) -> WorkOrder:
    work_order.work_order_id = _next_work_order_id(session)
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
