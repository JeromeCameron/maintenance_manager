from sqlmodel import Session

import crud.workOrders as wo_crud
from schema.models import WorkOrder, WorkOrderPart, WorkOrderStatus


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
