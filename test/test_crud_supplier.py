from sqlmodel import Session

import crud.supplier as supplier_crud
from schema.models import Supplier


def make_supplier(name: str = "Acme Parts") -> Supplier:
    return Supplier(
        name=name,
        address="123 Main St, Kingston",
        primary_contact="Bob Jones",
        email="bob@acme.com",
    )


class TestSupplier:
    def test_add_supplier(self, session: Session):
        supplier = supplier_crud.add_supplier(session, make_supplier())
        assert supplier.supplier_id is not None
        assert supplier.name == "Acme Parts"

    def test_get_suppliers_empty(self, session: Session):
        assert supplier_crud.get_suppliers(session) == []

    def test_get_suppliers(self, session: Session):
        supplier_crud.add_supplier(session, make_supplier("Supplier A"))
        supplier_crud.add_supplier(session, make_supplier("Supplier B"))
        assert len(supplier_crud.get_suppliers(session)) == 2

    def test_get_supplier(self, session: Session):
        added = supplier_crud.add_supplier(session, make_supplier())
        result = supplier_crud.get_supplier(session, added.supplier_id)
        assert result is not None
        assert result.supplier_id == added.supplier_id

    def test_get_supplier_not_found(self, session: Session):
        assert supplier_crud.get_supplier(session, 999) is None

    def test_update_supplier(self, session: Session):
        added = supplier_crud.add_supplier(session, make_supplier())
        updated = make_supplier()
        updated.primary_contact = "Alice Wong"
        result = supplier_crud.update_supplier(session, added.supplier_id, updated)
        assert result is not None
        assert result.primary_contact == "Alice Wong"

    def test_update_supplier_not_found(self, session: Session):
        assert supplier_crud.update_supplier(session, 999, make_supplier()) is None

    def test_delete_supplier(self, session: Session):
        added = supplier_crud.add_supplier(session, make_supplier())
        assert supplier_crud.delete_supplier(session, added.supplier_id) is True
        assert supplier_crud.get_supplier(session, added.supplier_id) is None

    def test_delete_supplier_not_found(self, session: Session):
        assert supplier_crud.delete_supplier(session, 999) is False
