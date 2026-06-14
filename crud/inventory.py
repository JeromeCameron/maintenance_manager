from datetime import datetime
from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import EquipmentPart, Part, PartCategory, PartSupplier, StockLevel, StockTransaction, TransactionType


def _apply_transaction(session: Session, tx: StockTransaction, reverse: bool = False) -> None:
    """Apply (or reverse) a transaction's quantity delta to the matching StockLevel row."""
    if not tx.part_no:
        return

    stmt = select(StockLevel).where(StockLevel.part_no == tx.part_no)
    stmt = stmt.where(
        StockLevel.location_id == tx.location_id if tx.location_id is not None
        else StockLevel.location_id.is_(None)  # type: ignore[union-attr]
    )
    sl = session.exec(stmt).first()

    if sl is None:
        sl = StockLevel(part_no=tx.part_no, location_id=tx.location_id, quantity=0)

    if tx.transaction_type == TransactionType.issue:
        delta = -tx.quantity
    else:
        delta = tx.quantity  # receive or adjust (adjust can be negative)

    sl.quantity += -delta if reverse else delta
    sl.last_updated = datetime.now()
    session.add(sl)


# ------------------------------------------------------------------
# Part Category


def get_part_categories(session: Session) -> Sequence[PartCategory]:
    return session.exec(select(PartCategory)).all()


def get_part_category(session: Session, category_id: int) -> Optional[PartCategory]:
    return session.get(PartCategory, category_id)


def add_part_category(session: Session, category: PartCategory) -> PartCategory:
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def update_part_category(
    session: Session, category_id: int, data: PartCategory
) -> Optional[PartCategory]:
    db_category: Optional[PartCategory] = session.get(PartCategory, category_id)
    if db_category is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_category, key, value)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category


def delete_part_category(session: Session, category_id: int) -> bool:
    category = session.get(PartCategory, category_id)
    if category is None:
        return False
    session.delete(category)
    session.commit()
    return True


# ------------------------------------------------------------------
# Part


def get_parts(session: Session) -> Sequence[Part]:
    return session.exec(select(Part)).all()


def get_part(session: Session, part_no: str) -> Optional[Part]:
    return session.get(Part, part_no)


def add_part(session: Session, part: Part) -> Part:
    session.add(part)
    session.commit()
    session.refresh(part)
    return part


def update_part(session: Session, part_no: str, data: Part) -> Optional[Part]:
    db_part: Optional[Part] = session.get(Part, part_no)
    if db_part is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_part, key, value)
    session.add(db_part)
    session.commit()
    session.refresh(db_part)
    return db_part


def delete_part(session: Session, part_no: str) -> bool:
    part = session.get(Part, part_no)
    if part is None:
        return False
    session.delete(part)
    session.commit()
    return True


# ------------------------------------------------------------------
# Equipment Part


def get_equipment_parts(session: Session) -> Sequence[EquipmentPart]:
    return session.exec(select(EquipmentPart)).all()


def get_equipment_part(session: Session, equipment_part_id: int) -> Optional[EquipmentPart]:
    return session.get(EquipmentPart, equipment_part_id)


def get_equipment_parts_by_part(session: Session, part_no: str) -> Sequence[EquipmentPart]:
    return session.exec(select(EquipmentPart).where(EquipmentPart.part_no == part_no)).all()


def add_equipment_part(session: Session, equipment_part: EquipmentPart) -> EquipmentPart:
    session.add(equipment_part)
    session.commit()
    session.refresh(equipment_part)
    return equipment_part


def update_equipment_part(
    session: Session, equipment_part_id: int, data: EquipmentPart
) -> Optional[EquipmentPart]:
    db_ep: Optional[EquipmentPart] = session.get(EquipmentPart, equipment_part_id)
    if db_ep is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_ep, key, value)
    session.add(db_ep)
    session.commit()
    session.refresh(db_ep)
    return db_ep


def delete_equipment_part(session: Session, equipment_part_id: int) -> bool:
    ep = session.get(EquipmentPart, equipment_part_id)
    if ep is None:
        return False
    session.delete(ep)
    session.commit()
    return True


# ------------------------------------------------------------------
# Part Supplier


def get_part_suppliers(session: Session) -> Sequence[PartSupplier]:
    return session.exec(select(PartSupplier)).all()


def get_part_supplier(session: Session, part_supplier_id: int) -> Optional[PartSupplier]:
    return session.get(PartSupplier, part_supplier_id)


def get_part_suppliers_by_part(session: Session, part_no: str) -> Sequence[PartSupplier]:
    return session.exec(select(PartSupplier).where(PartSupplier.part_no == part_no)).all()


def add_part_supplier(session: Session, part_supplier: PartSupplier) -> PartSupplier:
    session.add(part_supplier)
    session.commit()
    session.refresh(part_supplier)
    return part_supplier


def update_part_supplier(
    session: Session, part_supplier_id: int, data: PartSupplier
) -> Optional[PartSupplier]:
    db_ps: Optional[PartSupplier] = session.get(PartSupplier, part_supplier_id)
    if db_ps is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_ps, key, value)
    session.add(db_ps)
    session.commit()
    session.refresh(db_ps)
    return db_ps


def delete_part_supplier(session: Session, part_supplier_id: int) -> bool:
    ps = session.get(PartSupplier, part_supplier_id)
    if ps is None:
        return False
    session.delete(ps)
    session.commit()
    return True


# ------------------------------------------------------------------
# Stock Level


def get_stock_levels(session: Session) -> Sequence[StockLevel]:
    return session.exec(select(StockLevel)).all()


def get_stock_level(session: Session, stock_level_id: int) -> Optional[StockLevel]:
    return session.get(StockLevel, stock_level_id)


def add_stock_level(session: Session, stock_level: StockLevel) -> StockLevel:
    session.add(stock_level)
    session.commit()
    session.refresh(stock_level)
    return stock_level


def update_stock_level(
    session: Session, stock_level_id: int, data: StockLevel
) -> Optional[StockLevel]:
    db_sl: Optional[StockLevel] = session.get(StockLevel, stock_level_id)
    if db_sl is None:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_sl, key, value)
    session.add(db_sl)
    session.commit()
    session.refresh(db_sl)
    return db_sl


def delete_stock_level(session: Session, stock_level_id: int) -> bool:
    sl = session.get(StockLevel, stock_level_id)
    if sl is None:
        return False
    session.delete(sl)
    session.commit()
    return True


# ------------------------------------------------------------------
# Stock Transaction


def get_stock_transactions(session: Session) -> Sequence[StockTransaction]:
    return session.exec(select(StockTransaction)).all()


def get_stock_transaction(session: Session, transaction_id: int) -> Optional[StockTransaction]:
    return session.get(StockTransaction, transaction_id)


def add_stock_transaction(session: Session, transaction: StockTransaction) -> StockTransaction:
    session.add(transaction)
    _apply_transaction(session, transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


def update_stock_transaction(
    session: Session, transaction_id: int, data: StockTransaction
) -> Optional[StockTransaction]:
    db_tx: Optional[StockTransaction] = session.get(StockTransaction, transaction_id)
    if db_tx is None:
        return None
    _apply_transaction(session, db_tx, reverse=True)  # undo old
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_tx, key, value)
    _apply_transaction(session, db_tx)  # apply new
    session.add(db_tx)
    session.commit()
    session.refresh(db_tx)
    return db_tx


def delete_stock_transaction(session: Session, transaction_id: int) -> bool:
    tx = session.get(StockTransaction, transaction_id)
    if tx is None:
        return False
    _apply_transaction(session, tx, reverse=True)  # undo
    session.delete(tx)
    session.commit()
    return True


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
