from typing import Optional, Sequence

from sqlmodel import Session, select

from schema.models import Supplier, SupplierCategoryLink, SupplierCategory, SupplierInput, SupplierRead


def _to_read(session: Session, supplier: Supplier) -> SupplierRead:
    links = session.exec(
        select(SupplierCategoryLink).where(SupplierCategoryLink.supplier_id == supplier.supplier_id)
    ).all()
    return SupplierRead(
        supplier_id=supplier.supplier_id,
        name=supplier.name,
        address=supplier.address,
        primary_contact=supplier.primary_contact,
        email=supplier.email,
        contact_number=supplier.contact_number,
        contact_title=supplier.contact_title,
        notes=supplier.notes,
        categories=[link.category.value for link in links],
    )


def _set_categories(session: Session, supplier_id: int, categories: list[str]) -> None:
    existing = session.exec(
        select(SupplierCategoryLink).where(SupplierCategoryLink.supplier_id == supplier_id)
    ).all()
    for link in existing:
        session.delete(link)
    session.flush()
    for cat in categories:
        session.add(SupplierCategoryLink(supplier_id=supplier_id, category=SupplierCategory(cat)))


def get_suppliers(session: Session) -> list[SupplierRead]:
    suppliers = session.exec(select(Supplier)).all()
    return [_to_read(session, s) for s in suppliers]


def get_supplier(session: Session, supplier_id: int) -> Optional[SupplierRead]:
    supplier = session.get(Supplier, supplier_id)
    if supplier is None:
        return None
    return _to_read(session, supplier)


def add_supplier(session: Session, data: SupplierInput) -> SupplierRead:
    supplier = Supplier(
        name=data.name,
        address=data.address,
        primary_contact=data.primary_contact,
        email=data.email,
        contact_number=data.contact_number,
        contact_title=data.contact_title,
        notes=data.notes,
    )
    session.add(supplier)
    session.flush()
    _set_categories(session, supplier.supplier_id, data.categories)
    session.commit()
    session.refresh(supplier)
    return _to_read(session, supplier)


def update_supplier(session: Session, supplier_id: int, data: SupplierInput) -> Optional[SupplierRead]:
    supplier = session.get(Supplier, supplier_id)
    if supplier is None:
        return None
    for field in ("name", "address", "primary_contact", "email", "contact_number", "contact_title", "notes"):
        value = getattr(data, field, None)
        if value is not None:
            setattr(supplier, field, value)
    session.add(supplier)
    _set_categories(session, supplier_id, data.categories)
    session.commit()
    session.refresh(supplier)
    return _to_read(session, supplier)


def delete_supplier(session: Session, supplier_id: int) -> bool:
    supplier = session.get(Supplier, supplier_id)
    if supplier is None:
        return False
    session.delete(supplier)
    session.commit()
    return True


if __name__ == "__main__":
    raise NotImplementedError("This functionality is not implemented.")
