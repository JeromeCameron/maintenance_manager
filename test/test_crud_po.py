from sqlmodel import Session

import crud.po as po_crud
from schema.models import PurchaseOrder, PurchaseOrderType


def make_po(po_no: str = "PO-001", asset_id: str | None = None) -> PurchaseOrder:
    return PurchaseOrder(
        po_no=po_no,
        subtotal=3000.00,
        po_type=PurchaseOrderType.corrective,
        asset_id=asset_id,
    )


class TestPurchaseOrder:
    def test_add_purchase_order(self, session: Session):
        po = po_crud.add_purchase_order(session, make_po())
        assert po.po_no == "PO-001"
        assert po.subtotal == 3000.00

    def test_get_purchase_orders_empty(self, session: Session):
        assert po_crud.get_purchase_orders(session) == []

    def test_get_purchase_orders(self, session: Session):
        po_crud.add_purchase_order(session, make_po("PO-001"))
        po_crud.add_purchase_order(session, make_po("PO-002"))
        assert len(po_crud.get_purchase_orders(session)) == 2

    def test_get_purchase_order(self, session: Session):
        po_crud.add_purchase_order(session, make_po())
        result = po_crud.get_purchase_order(session, "PO-001")
        assert result is not None
        assert result.po_no == "PO-001"

    def test_get_purchase_order_not_found(self, session: Session):
        assert po_crud.get_purchase_order(session, "MISSING") is None

    def test_update_purchase_order(self, session: Session):
        po_crud.add_purchase_order(session, make_po())
        updated = make_po()
        updated.subtotal = 4500.00
        result = po_crud.update_purchase_order(session, "PO-001", updated)
        assert result is not None
        assert result.subtotal == 4500.00

    def test_update_purchase_order_not_found(self, session: Session):
        assert po_crud.update_purchase_order(session, "MISSING", make_po()) is None

    def test_delete_purchase_order(self, session: Session):
        po_crud.add_purchase_order(session, make_po())
        assert po_crud.delete_purchase_order(session, "PO-001") is True
        assert po_crud.get_purchase_order(session, "PO-001") is None

    def test_delete_purchase_order_not_found(self, session: Session):
        assert po_crud.delete_purchase_order(session, "MISSING") is False

    def test_get_purchase_orders_by_asset(self, session: Session):
        po_crud.add_purchase_order(session, make_po("PO-001", asset_id="ASSET-001"))
        po_crud.add_purchase_order(session, make_po("PO-002", asset_id="ASSET-001"))
        po_crud.add_purchase_order(session, make_po("PO-003", asset_id="ASSET-002"))
        results = po_crud.get_purchase_orders_by_asset(session, "ASSET-001")
        assert len(results) == 2
        assert all(p.asset_id == "ASSET-001" for p in results)

    def test_get_purchase_orders_by_asset_empty(self, session: Session):
        po_crud.add_purchase_order(session, make_po("PO-001", asset_id="ASSET-002"))
        results = po_crud.get_purchase_orders_by_asset(session, "ASSET-001")
        assert results == []
