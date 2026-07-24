from sqlmodel import Session, select

import crud.inventory as inventory_crud
import crud.workOrders as wo_crud
from schema.models import (
    Part,
    StockLevel,
    StockTransaction,
    TransactionType,
    UnitMeasure,
    WorkOrder,
    WorkOrderPart,
    WorkOrderStatus,
)


def make_work_order(asset_id: str | None = None) -> WorkOrder:
    return WorkOrder(
        priority="High",
        typ="Corrective",
        asset_id=asset_id,
        status=WorkOrderStatus.requested,
    )


def make_work_order_part(work_order_id: int | None = None) -> WorkOrderPart:
    return WorkOrderPart(
        work_order_id=work_order_id,
        quantity_used=2,
        unit_cost=150.00,
    )


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


class TestWorkOrder:
    def test_add_work_order(self, session: Session):
        wo = wo_crud.add_work_order(session, make_work_order())
        assert wo.work_order_id is not None
        assert wo.priority == "High"

    def test_get_work_orders_empty(self, session: Session):
        assert wo_crud.get_work_orders(session) == []

    def test_get_work_orders(self, session: Session):
        wo_crud.add_work_order(session, make_work_order())
        wo_crud.add_work_order(session, make_work_order())
        assert len(wo_crud.get_work_orders(session)) == 2

    def test_get_work_order(self, session: Session):
        added = wo_crud.add_work_order(session, make_work_order())
        result = wo_crud.get_work_order(session, added.work_order_id)
        assert result is not None
        assert result.work_order_id == added.work_order_id

    def test_get_work_order_not_found(self, session: Session):
        assert wo_crud.get_work_order(session, 999) is None

    def test_update_work_order(self, session: Session):
        added = wo_crud.add_work_order(session, make_work_order())
        updated = make_work_order()
        updated.priority = "Low"
        result = wo_crud.update_work_order(session, added.work_order_id, updated)
        assert result is not None
        assert result.priority == "Low"

    def test_update_work_order_not_found(self, session: Session):
        assert wo_crud.update_work_order(session, 999, make_work_order()) is None

    def test_delete_work_order(self, session: Session):
        added = wo_crud.add_work_order(session, make_work_order())
        assert wo_crud.delete_work_order(session, added.work_order_id) is True
        assert wo_crud.get_work_order(session, added.work_order_id) is None

    def test_delete_work_order_not_found(self, session: Session):
        assert wo_crud.delete_work_order(session, 999) is False

    def test_get_work_orders_by_asset(self, session: Session):
        wo_crud.add_work_order(session, make_work_order(asset_id="ASSET-001"))
        wo_crud.add_work_order(session, make_work_order(asset_id="ASSET-001"))
        wo_crud.add_work_order(session, make_work_order(asset_id="ASSET-002"))
        results = wo_crud.get_work_orders_by_asset(session, "ASSET-001")
        assert len(results) == 2
        assert all(w.asset_id == "ASSET-001" for w in results)

    def test_get_work_orders_by_asset_empty(self, session: Session):
        wo_crud.add_work_order(session, make_work_order(asset_id="ASSET-002"))
        results = wo_crud.get_work_orders_by_asset(session, "ASSET-001")
        assert results == []


class TestWorkOrderPart:
    def test_add_work_order_part(self, session: Session):
        wop = wo_crud.add_work_order_part(session, make_work_order_part())
        assert wop.id is not None
        assert wop.quantity_used == 2
        assert wop.unit_cost == 150.00

    def test_get_work_order_parts_empty(self, session: Session):
        assert wo_crud.get_work_order_parts(session) == []

    def test_get_work_order_parts(self, session: Session):
        wo_crud.add_work_order_part(session, make_work_order_part())
        wo_crud.add_work_order_part(session, make_work_order_part())
        assert len(wo_crud.get_work_order_parts(session)) == 2

    def test_get_work_order_part(self, session: Session):
        added = wo_crud.add_work_order_part(session, make_work_order_part())
        result = wo_crud.get_work_order_part(session, added.id)
        assert result is not None
        assert result.id == added.id

    def test_get_work_order_part_not_found(self, session: Session):
        assert wo_crud.get_work_order_part(session, 999) is None

    def test_update_work_order_part(self, session: Session):
        added = wo_crud.add_work_order_part(session, make_work_order_part())
        updated = make_work_order_part()
        updated.quantity_used = 5
        result = wo_crud.update_work_order_part(session, added.id, updated)
        assert result is not None
        assert result.quantity_used == 5

    def test_update_work_order_part_not_found(self, session: Session):
        assert wo_crud.update_work_order_part(session, 999, make_work_order_part()) is None

    def test_delete_work_order_part(self, session: Session):
        added = wo_crud.add_work_order_part(session, make_work_order_part())
        assert wo_crud.delete_work_order_part(session, added.id) is True
        assert wo_crud.get_work_order_part(session, added.id) is None

    def test_delete_work_order_part_not_found(self, session: Session):
        assert wo_crud.delete_work_order_part(session, 999) is False


class TestWorkOrderPartStockSync:
    """Checking a part out on a work order should auto-generate the matching
    stock 'issue' transaction instead of requiring a separate manual entry."""

    def test_add_creates_linked_issue_transaction(self, session: Session):
        inventory_crud.add_part(session, make_part())
        wo = wo_crud.add_work_order(session, make_work_order())
        wop = wo_crud.add_work_order_part(
            session, WorkOrderPart(work_order_id=wo.work_order_id, part_no="P-001", quantity_used=4)
        )

        assert wop.stock_transaction_id is not None
        tx = session.get(StockTransaction, wop.stock_transaction_id)
        assert tx is not None
        assert tx.transaction_type == TransactionType.issue
        assert tx.quantity == 4
        assert tx.part_no == "P-001"
        assert tx.work_order_id == wo.work_order_id

        sl = session.exec(select(StockLevel).where(StockLevel.part_no == "P-001")).first()
        assert sl is not None
        assert sl.quantity == -4  # no receipts yet, so this goes negative

    def test_add_without_part_no_creates_no_transaction(self, session: Session):
        wop = wo_crud.add_work_order_part(session, make_work_order_part())
        assert wop.stock_transaction_id is None
        assert wo_crud.get_work_order_parts(session)  # sanity: row still created

    def test_update_quantity_adjusts_linked_transaction(self, session: Session):
        inventory_crud.add_part(session, make_part())
        wo = wo_crud.add_work_order(session, make_work_order())
        wop = wo_crud.add_work_order_part(
            session, WorkOrderPart(work_order_id=wo.work_order_id, part_no="P-001", quantity_used=4)
        )

        updated = wo_crud.update_work_order_part(
            session, wop.id, WorkOrderPart(part_no="P-001", quantity_used=10)
        )

        assert updated.stock_transaction_id == wop.stock_transaction_id  # same tx, adjusted in place
        tx = session.get(StockTransaction, updated.stock_transaction_id)
        assert tx.quantity == 10

        sl = session.exec(select(StockLevel).where(StockLevel.part_no == "P-001")).first()
        assert sl.quantity == -10

    def test_delete_reverses_and_removes_linked_transaction(self, session: Session):
        inventory_crud.add_part(session, make_part())
        wo = wo_crud.add_work_order(session, make_work_order())
        wop = wo_crud.add_work_order_part(
            session, WorkOrderPart(work_order_id=wo.work_order_id, part_no="P-001", quantity_used=4)
        )
        tx_id = wop.stock_transaction_id

        assert wo_crud.delete_work_order_part(session, wop.id) is True

        assert session.get(StockTransaction, tx_id) is None
        sl = session.exec(select(StockLevel).where(StockLevel.part_no == "P-001")).first()
        assert sl.quantity == 0
