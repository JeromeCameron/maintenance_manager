from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import PurchaseOrder


def get_purchase_orders(session: Session) -> Sequence[PurchaseOrder]:
    statement = select(PurchaseOrder)
    results = session.exec(statement).all()
    return results


def get_purchase_order(session: Session, po_no: str) -> Optional[PurchaseOrder]:
    po = session.get(PurchaseOrder, po_no)
    return po


def add_purchase_order(session: Session, po: PurchaseOrder) -> PurchaseOrder:
    session.add(po)
    session.commit()
    session.refresh(po)
    return po


def update_purchase_order(
    session: Session, po_no: str, data: PurchaseOrder
) -> Optional[PurchaseOrder]:
    db_po: Optional[PurchaseOrder] = session.get(PurchaseOrder, po_no)

    if db_po is None:
        return None

    po = data.model_dump(exclude_unset=True)
    for key, value in po.items():
        setattr(db_po, key, value)

    session.add(db_po)
    session.commit()
    session.refresh(db_po)
    return db_po


def delete_purchase_order(session: Session, po_no: str) -> bool:
    po = session.get(PurchaseOrder, po_no)
    if po is None:
        return False
    session.delete(po)
    session.commit()
    return True


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
