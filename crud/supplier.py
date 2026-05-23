from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import Supplier


def get_suppliers(session: Session) -> Sequence[Supplier]:
    statement = select(Supplier)
    results = session.exec(statement).all()
    return results


def get_supplier(session: Session, supplier_id: int) -> Optional[Supplier]:
    supplier = session.get(Supplier, supplier_id)
    return supplier


def add_supplier(session: Session, supplier: Supplier) -> Supplier:
    session.add(supplier)
    session.commit()
    session.refresh(supplier)
    return supplier


def update_supplier(
    session: Session, supplier_id: int, data: Supplier
) -> Optional[Supplier]:
    db_spplier: Optional[Supplier] = session.get(Supplier, supplier_id)

    if db_spplier is None:
        return None

    supplier = data.model_dump(exclude_unset=True)
    for key, value in supplier.items():
        setattr(db_spplier, key, value)

    session.add(db_spplier)
    session.commit()
    session.refresh(db_spplier)
    return db_spplier


def delete_supplier(session: Session, supplier_id: int) -> bool:
    supplier = session.get(Supplier, supplier_id)
    if supplier is None:
        return False
    session.delete(supplier)
    session.commit()
    return True


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
