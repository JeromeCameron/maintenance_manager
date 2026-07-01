from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import Invoice


def get_invoices(session: Session) -> Sequence[Invoice]:
    statement = select(Invoice)
    results = session.exec(statement).all()
    return results


def get_invoices_by_supplier(session: Session, supplier_id: int) -> Sequence[Invoice]:
    return session.exec(select(Invoice).where(Invoice.supplier_id == supplier_id)).all()


def get_invoice(session: Session, id: int) -> Optional[Invoice]:
    invoice = session.get(Invoice, id)
    return invoice


def add_invoice(session: Session, invoice: Invoice) -> Invoice:
    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    return invoice


def update_invoice(session: Session, id: int, data: Invoice) -> Optional[Invoice]:
    db_invoice: Optional[Invoice] = session.get(Invoice, id)

    if db_invoice is None:
        return None

    invoice = data.model_dump(exclude_unset=True)
    for key, value in invoice.items():
        setattr(db_invoice, key, value)

    session.add(db_invoice)
    session.commit()
    session.refresh(db_invoice)
    return db_invoice


def delete_invoice(session: Session, id: int) -> bool:
    invoice = session.get(Invoice, id)
    if invoice is None:
        return False
    session.delete(invoice)
    session.commit()
    return True


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
