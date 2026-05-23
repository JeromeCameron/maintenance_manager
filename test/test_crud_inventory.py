from sqlmodel import Session

import crud.inventory as inventory_crud
from schema.models import (
    EquipmentPart,
    Part,
    PartCategory,
    PartSupplier,
    StockLevel,
    StockTransaction,
    TransactionType,
    UnitMeasure,
)


def make_part_category(name: str = "Hydraulics") -> PartCategory:
    return PartCategory(name=name)


def make_part(part_no: str = "P-001") -> Part:
    return Part(
        part_no=part_no,
        part_name="Hydraulic Seal",
        unit_of_measure=UnitMeasure.unit,
        min_level=5,
        max_level=50,
        reorder_level=10,
        reorder_qty=20,
    )


def make_equipment_part() -> EquipmentPart:
    return EquipmentPart(is_critical=True)


def make_part_supplier() -> PartSupplier:
    return PartSupplier(lead_time_days=7, last_cost=25.00)


def make_stock_level() -> StockLevel:
    return StockLevel(quantity=30)


def make_stock_transaction() -> StockTransaction:
    return StockTransaction(
        transaction_type=TransactionType.receive,
        quantity=10,
    )


class TestPartCategory:
    def test_add_part_category(self, session: Session):
        cat = inventory_crud.add_part_category(session, make_part_category())
        assert cat.id is not None
        assert cat.name == "Hydraulics"

    def test_get_part_categories_empty(self, session: Session):
        assert inventory_crud.get_part_categories(session) == []

    def test_get_part_categories(self, session: Session):
        inventory_crud.add_part_category(session, make_part_category("Cat A"))
        inventory_crud.add_part_category(session, make_part_category("Cat B"))
        assert len(inventory_crud.get_part_categories(session)) == 2

    def test_get_part_category(self, session: Session):
        added = inventory_crud.add_part_category(session, make_part_category())
        result = inventory_crud.get_part_category(session, added.id)
        assert result is not None
        assert result.id == added.id

    def test_get_part_category_not_found(self, session: Session):
        assert inventory_crud.get_part_category(session, 999) is None

    def test_update_part_category(self, session: Session):
        added = inventory_crud.add_part_category(session, make_part_category())
        updated = make_part_category()
        updated.name = "Electrical"
        result = inventory_crud.update_part_category(session, added.id, updated)
        assert result is not None
        assert result.name == "Electrical"

    def test_update_part_category_not_found(self, session: Session):
        assert inventory_crud.update_part_category(session, 999, make_part_category()) is None

    def test_delete_part_category(self, session: Session):
        added = inventory_crud.add_part_category(session, make_part_category())
        assert inventory_crud.delete_part_category(session, added.id) is True
        assert inventory_crud.get_part_category(session, added.id) is None

    def test_delete_part_category_not_found(self, session: Session):
        assert inventory_crud.delete_part_category(session, 999) is False


class TestPart:
    def test_add_part(self, session: Session):
        part = inventory_crud.add_part(session, make_part())
        assert part.part_no == "P-001"
        assert part.part_name == "Hydraulic Seal"

    def test_get_parts_empty(self, session: Session):
        assert inventory_crud.get_parts(session) == []

    def test_get_parts(self, session: Session):
        inventory_crud.add_part(session, make_part("P-001"))
        inventory_crud.add_part(session, make_part("P-002"))
        assert len(inventory_crud.get_parts(session)) == 2

    def test_get_part(self, session: Session):
        inventory_crud.add_part(session, make_part())
        result = inventory_crud.get_part(session, "P-001")
        assert result is not None
        assert result.part_no == "P-001"

    def test_get_part_not_found(self, session: Session):
        assert inventory_crud.get_part(session, "MISSING") is None

    def test_update_part(self, session: Session):
        inventory_crud.add_part(session, make_part())
        updated = make_part()
        updated.part_name = "Updated Seal"
        result = inventory_crud.update_part(session, "P-001", updated)
        assert result is not None
        assert result.part_name == "Updated Seal"

    def test_update_part_not_found(self, session: Session):
        assert inventory_crud.update_part(session, "MISSING", make_part()) is None

    def test_delete_part(self, session: Session):
        inventory_crud.add_part(session, make_part())
        assert inventory_crud.delete_part(session, "P-001") is True
        assert inventory_crud.get_part(session, "P-001") is None

    def test_delete_part_not_found(self, session: Session):
        assert inventory_crud.delete_part(session, "MISSING") is False


class TestEquipmentPart:
    def test_add_equipment_part(self, session: Session):
        ep = inventory_crud.add_equipment_part(session, make_equipment_part())
        assert ep.id is not None
        assert ep.is_critical is True

    def test_get_equipment_parts_empty(self, session: Session):
        assert inventory_crud.get_equipment_parts(session) == []

    def test_get_equipment_parts(self, session: Session):
        inventory_crud.add_equipment_part(session, make_equipment_part())
        inventory_crud.add_equipment_part(session, make_equipment_part())
        assert len(inventory_crud.get_equipment_parts(session)) == 2

    def test_get_equipment_part(self, session: Session):
        added = inventory_crud.add_equipment_part(session, make_equipment_part())
        result = inventory_crud.get_equipment_part(session, added.id)
        assert result is not None
        assert result.id == added.id

    def test_get_equipment_part_not_found(self, session: Session):
        assert inventory_crud.get_equipment_part(session, 999) is None

    def test_update_equipment_part(self, session: Session):
        added = inventory_crud.add_equipment_part(session, make_equipment_part())
        updated = make_equipment_part()
        updated.is_critical = False
        result = inventory_crud.update_equipment_part(session, added.id, updated)
        assert result is not None
        assert result.is_critical is False

    def test_update_equipment_part_not_found(self, session: Session):
        assert inventory_crud.update_equipment_part(session, 999, make_equipment_part()) is None

    def test_delete_equipment_part(self, session: Session):
        added = inventory_crud.add_equipment_part(session, make_equipment_part())
        assert inventory_crud.delete_equipment_part(session, added.id) is True
        assert inventory_crud.get_equipment_part(session, added.id) is None

    def test_delete_equipment_part_not_found(self, session: Session):
        assert inventory_crud.delete_equipment_part(session, 999) is False


class TestPartSupplier:
    def test_add_part_supplier(self, session: Session):
        ps = inventory_crud.add_part_supplier(session, make_part_supplier())
        assert ps.id is not None
        assert ps.lead_time_days == 7

    def test_get_part_suppliers_empty(self, session: Session):
        assert inventory_crud.get_part_suppliers(session) == []

    def test_get_part_suppliers(self, session: Session):
        inventory_crud.add_part_supplier(session, make_part_supplier())
        inventory_crud.add_part_supplier(session, make_part_supplier())
        assert len(inventory_crud.get_part_suppliers(session)) == 2

    def test_get_part_supplier(self, session: Session):
        added = inventory_crud.add_part_supplier(session, make_part_supplier())
        result = inventory_crud.get_part_supplier(session, added.id)
        assert result is not None
        assert result.id == added.id

    def test_get_part_supplier_not_found(self, session: Session):
        assert inventory_crud.get_part_supplier(session, 999) is None

    def test_update_part_supplier(self, session: Session):
        added = inventory_crud.add_part_supplier(session, make_part_supplier())
        updated = make_part_supplier()
        updated.lead_time_days = 14
        result = inventory_crud.update_part_supplier(session, added.id, updated)
        assert result is not None
        assert result.lead_time_days == 14

    def test_update_part_supplier_not_found(self, session: Session):
        assert inventory_crud.update_part_supplier(session, 999, make_part_supplier()) is None

    def test_delete_part_supplier(self, session: Session):
        added = inventory_crud.add_part_supplier(session, make_part_supplier())
        assert inventory_crud.delete_part_supplier(session, added.id) is True
        assert inventory_crud.get_part_supplier(session, added.id) is None

    def test_delete_part_supplier_not_found(self, session: Session):
        assert inventory_crud.delete_part_supplier(session, 999) is False


class TestStockLevel:
    def test_add_stock_level(self, session: Session):
        sl = inventory_crud.add_stock_level(session, make_stock_level())
        assert sl.id is not None
        assert sl.quantity == 30

    def test_get_stock_levels_empty(self, session: Session):
        assert inventory_crud.get_stock_levels(session) == []

    def test_get_stock_levels(self, session: Session):
        inventory_crud.add_stock_level(session, make_stock_level())
        inventory_crud.add_stock_level(session, make_stock_level())
        assert len(inventory_crud.get_stock_levels(session)) == 2

    def test_get_stock_level(self, session: Session):
        added = inventory_crud.add_stock_level(session, make_stock_level())
        result = inventory_crud.get_stock_level(session, added.id)
        assert result is not None
        assert result.id == added.id

    def test_get_stock_level_not_found(self, session: Session):
        assert inventory_crud.get_stock_level(session, 999) is None

    def test_update_stock_level(self, session: Session):
        added = inventory_crud.add_stock_level(session, make_stock_level())
        updated = make_stock_level()
        updated.quantity = 50
        result = inventory_crud.update_stock_level(session, added.id, updated)
        assert result is not None
        assert result.quantity == 50

    def test_update_stock_level_not_found(self, session: Session):
        assert inventory_crud.update_stock_level(session, 999, make_stock_level()) is None

    def test_delete_stock_level(self, session: Session):
        added = inventory_crud.add_stock_level(session, make_stock_level())
        assert inventory_crud.delete_stock_level(session, added.id) is True
        assert inventory_crud.get_stock_level(session, added.id) is None

    def test_delete_stock_level_not_found(self, session: Session):
        assert inventory_crud.delete_stock_level(session, 999) is False


class TestStockTransaction:
    def test_add_stock_transaction(self, session: Session):
        tx = inventory_crud.add_stock_transaction(session, make_stock_transaction())
        assert tx.id is not None
        assert tx.transaction_type == TransactionType.receive
        assert tx.quantity == 10

    def test_get_stock_transactions_empty(self, session: Session):
        assert inventory_crud.get_stock_transactions(session) == []

    def test_get_stock_transactions(self, session: Session):
        inventory_crud.add_stock_transaction(session, make_stock_transaction())
        inventory_crud.add_stock_transaction(session, make_stock_transaction())
        assert len(inventory_crud.get_stock_transactions(session)) == 2

    def test_get_stock_transaction(self, session: Session):
        added = inventory_crud.add_stock_transaction(session, make_stock_transaction())
        result = inventory_crud.get_stock_transaction(session, added.id)
        assert result is not None
        assert result.id == added.id

    def test_get_stock_transaction_not_found(self, session: Session):
        assert inventory_crud.get_stock_transaction(session, 999) is None

    def test_update_stock_transaction(self, session: Session):
        added = inventory_crud.add_stock_transaction(session, make_stock_transaction())
        updated = make_stock_transaction()
        updated.quantity = 25
        result = inventory_crud.update_stock_transaction(session, added.id, updated)
        assert result is not None
        assert result.quantity == 25

    def test_update_stock_transaction_not_found(self, session: Session):
        assert inventory_crud.update_stock_transaction(session, 999, make_stock_transaction()) is None

    def test_delete_stock_transaction(self, session: Session):
        added = inventory_crud.add_stock_transaction(session, make_stock_transaction())
        assert inventory_crud.delete_stock_transaction(session, added.id) is True
        assert inventory_crud.get_stock_transaction(session, added.id) is None

    def test_delete_stock_transaction_not_found(self, session: Session):
        assert inventory_crud.delete_stock_transaction(session, 999) is False
