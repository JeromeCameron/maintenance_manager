"""
Import data from spreadsheets in data_files/ into the database.

Usage:
    uv run python data_imports.py
"""

import math
from datetime import date
from pathlib import Path

import openpyxl

from schema.database import engine
from schema.models import Asset, AssetCategory, AssetOwnership, AssetStatus, AssetSubStatus, WorkOrder, WorkOrderStatus, PurchaseOrder, PurchaseOrderType, Invoice, InvoiceStatus, InvoiceType
from sqlmodel import Session, text


DATA_DIR = Path(__file__).parent / "data_files"


def _to_enum(enum_cls, value):
    """Return enum member for value, or None if value is None/unrecognised."""
    if value is None:
        return None
    try:
        return enum_cls(str(value).strip().lower())
    except ValueError:
        return None


def _to_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def import_assets(session: Session) -> None:
    path = DATA_DIR / "tbl_assets_pure.xlsx"
    wb = openpyxl.load_workbook(path)
    ws = wb.active

    headers = [cell.value for cell in ws[1]]

    inserted = updated = skipped = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        data = dict(zip(headers, row))

        asset_id = data.get("asset_id")
        if not asset_id:
            skipped += 1
            continue

        asset = Asset(
            asset_id=str(asset_id).strip(),
            manufacturer=str(data["manufacturer"]).strip() if data.get("manufacturer") else "",
            model_no=str(data["model_no"]).strip() if data.get("model_no") else None,
            yr=int(data["yr"]) if data.get("yr") is not None else None,
            serial_no=str(data["serial_no"]).strip() if data.get("serial_no") else None,
            category=_to_enum(AssetCategory, data.get("category")),
            owned=_to_enum(AssetOwnership, data.get("owned")) or AssetOwnership.owned,
            alias=str(data["alias"]).strip() if data.get("alias") else None,
            date_in_service=_to_date(data.get("date_in_service")),
            status=_to_enum(AssetStatus, data.get("status")) or AssetStatus.operational,
            sub_status=_to_enum(AssetSubStatus, data.get("sub_status")),
            notes=str(data["notes"]).strip() if data.get("notes") else None,
            location_id=int(data["location"]) if data.get("location") is not None else None,
        )

        existing = session.get(Asset, asset.asset_id)
        session.merge(asset)

        if existing:
            updated += 1
        else:
            inserted += 1

    session.commit()
    print(f"Assets — inserted: {inserted}, updated: {updated}, skipped: {skipped}")


def _to_float(value) -> float | None:
    if value is None:
        return None
    try:
        f = float(value)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def _to_int(value) -> int | None:
    f = _to_float(value)
    return None if f is None else int(f)


def _to_bool(value) -> bool | None:
    f = _to_float(value)
    if f is None:
        return None
    return bool(f)


_PRIORITY_MAP = {"urgent": "High", "high": "High", "medium": "Medium", "low": "Low"}
_TYPE_MAP = {"preventative": "preventative", "corrective": "corrective", "predictive": "predictive"}


def import_work_orders(session: Session) -> None:
    path = DATA_DIR / "tbl_workOrders.xlsx"
    wb = openpyxl.load_workbook(path)
    ws = wb.active

    headers = [cell.value for cell in ws[1]]

    # Build sets of valid FK values to avoid constraint errors
    valid_assets = {row[0] for row in session.exec(text("SELECT asset_id FROM asset")).all()}  # type: ignore
    valid_suppliers = {row[0] for row in session.exec(text("SELECT supplier_id FROM supplier")).all()}  # type: ignore

    inserted = updated = skipped = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        data = dict(zip(headers, row))

        wo_id = _to_int(data.get("work_order_id"))
        if wo_id is None:
            skipped += 1
            continue

        priority_raw = str(data.get("priority") or "").strip().lower()
        priority = _PRIORITY_MAP.get(priority_raw, "Low")

        typ_raw = str(data.get("typ") or "").strip().lower()
        typ = _TYPE_MAP.get(typ_raw, typ_raw)

        status_raw = str(data.get("status") or "").strip().lower()
        try:
            status = WorkOrderStatus(status_raw)
        except ValueError:
            status = WorkOrderStatus.requested

        asset_id = str(data["asset_id"]).strip() if data.get("asset_id") else None
        if asset_id and asset_id not in valid_assets:
            asset_id = None

        supplier_id = _to_int(data.get("supplier_id"))
        if supplier_id and supplier_id not in valid_suppliers:
            supplier_id = None

        wo = WorkOrder(
            work_order_id=wo_id,
            issue_date=_to_date(data.get("issue_date")),
            priority=priority,
            typ=typ,
            asset_id=asset_id,
            asset_pm_id=_to_int(data.get("asset_pm_id")),
            description=str(data["description"]).strip() if data.get("description") else None,
            supplier_id=supplier_id,
            expected_date=_to_date(data.get("expected_date")),
            date_completed=_to_date(data.get("date_completed")),
            estimated_cost=_to_float(data.get("estimated_cost")),
            estimated_hours=_to_float(data.get("estimated_hours")),
            actual_cost=_to_float(data.get("actual_cost")),
            actual_hours=_to_float(data.get("actual_hours")),
            notes=str(data["notes"]).strip() if data.get("notes") else None,
            status=status,
            planned=_to_bool(data.get("planned")),
        )

        existing = session.get(WorkOrder, wo_id)
        session.merge(wo)

        if existing:
            updated += 1
        else:
            inserted += 1

    session.commit()

    # Advance the sequence past the highest imported ID
    max_id = session.exec(text("SELECT MAX(work_order_id) FROM workorder")).first()[0]  # type: ignore
    if max_id:
        session.exec(text(f"ALTER SEQUENCE workorder_work_order_id_seq RESTART WITH {max_id + 1}"))  # type: ignore
        session.commit()

    print(f"Work Orders — inserted: {inserted}, updated: {updated}, skipped: {skipped}")


def import_purchase_orders(session: Session) -> None:
    path = DATA_DIR / "tbl_po.xlsx"
    wb = openpyxl.load_workbook(path)
    ws = wb.active

    headers = [cell.value for cell in ws[1]]

    valid_assets = {row[0] for row in session.exec(text("SELECT asset_id FROM asset")).all()}  # type: ignore
    valid_suppliers = {row[0] for row in session.exec(text("SELECT supplier_id FROM supplier")).all()}  # type: ignore
    valid_locations = {row[0] for row in session.exec(text("SELECT location_id FROM location")).all()}  # type: ignore

    inserted = updated = skipped = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        data = dict(zip(headers, row))

        po_no = str(data.get("po_no") or "").strip()
        if not po_no:
            skipped += 1
            continue

        po_type_raw = str(data.get("po_type") or "").strip().lower()
        try:
            po_type = PurchaseOrderType(po_type_raw)
        except ValueError:
            po_type = PurchaseOrderType.purchase

        asset_id = str(data["asset_id"]).strip() if data.get("asset_id") else None
        if asset_id and asset_id not in valid_assets:
            asset_id = None

        supplier_id = _to_int(data.get("supplier_id"))
        if supplier_id and supplier_id not in valid_suppliers:
            supplier_id = None

        location_id = _to_int(data.get("location_id"))
        if location_id and location_id not in valid_locations:
            location_id = None

        po = PurchaseOrder(
            po_no=po_no,
            po_date=_to_date(data.get("po_date")),
            supplier_id=supplier_id,
            asset_id=asset_id,
            location_id=location_id,
            description=str(data["description"]).strip() if data.get("description") else None,
            subtotal=_to_float(data.get("subtotal")) or 0.0,
            po_type=po_type,
            cost_centre_id=None,
        )

        existing = session.get(PurchaseOrder, po_no)
        session.merge(po)

        if existing:
            updated += 1
        else:
            inserted += 1

    session.commit()
    print(f"Purchase Orders — inserted: {inserted}, updated: {updated}, skipped: {skipped}")


def import_invoices(session: Session) -> None:
    path = DATA_DIR / "tbl_invoices.xlsx"
    wb = openpyxl.load_workbook(path)
    ws = wb.active

    headers = [cell.value for cell in ws[1]]

    valid_suppliers = {row[0] for row in session.exec(text("SELECT supplier_id FROM supplier")).all()}  # type: ignore
    valid_assets = {row[0] for row in session.exec(text("SELECT asset_id FROM asset")).all()}  # type: ignore
    valid_locations = {row[0] for row in session.exec(text("SELECT location_id FROM location")).all()}  # type: ignore

    inserted = updated = skipped = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        data = dict(zip(headers, row))

        inv_id = _to_int(data.get("ID"))
        if inv_id is None:
            skipped += 1
            continue

        invoice_no = str(data.get("invoice_no") or "").strip()
        if not invoice_no:
            skipped += 1
            continue

        try:
            status = InvoiceStatus(str(data.get("status") or "").strip().lower())
        except ValueError:
            status = InvoiceStatus.submitted

        try:
            invoice_type = InvoiceType(str(data.get("invoice_type") or "").strip().lower())
        except ValueError:
            invoice_type = InvoiceType.services

        supplier_id = _to_int(data.get("supplier_id"))
        if supplier_id and supplier_id not in valid_suppliers:
            supplier_id = None

        asset_id = str(data["asset_id"]).strip() if data.get("asset_id") else None
        if asset_id and asset_id not in valid_assets:
            asset_id = None

        location_id = _to_int(data.get("location_id"))
        if location_id and location_id not in valid_locations:
            location_id = None

        tax_cert_val = data.get("tax_cert")
        if tax_cert_val is None:
            tax_cert = None
        elif isinstance(tax_cert_val, bool):
            tax_cert = tax_cert_val
        else:
            tax_cert = _to_bool(tax_cert_val)

        inv = Invoice(
            id=inv_id,
            invoice_no=invoice_no,
            invoice_date=_to_date(data.get("invoice_date")),
            job_date=_to_date(data.get("job_date")),
            rec_date=_to_date(data.get("rec_date")),
            supplier_id=supplier_id,
            work_order_id=None,
            asset_id=asset_id,
            location_id=location_id,
            description=str(data["description"]).strip() if data.get("description") else None,
            po_no=None,
            subtotal=_to_float(data.get("subtotal")) or 0.0,
            status=status,
            tax_cert=tax_cert,
            invoice_type=invoice_type,
        )

        existing = session.get(Invoice, inv_id)
        session.merge(inv)

        if existing:
            updated += 1
        else:
            inserted += 1

    session.commit()

    max_id = session.exec(text("SELECT MAX(id) FROM invoice")).first()[0]  # type: ignore
    if max_id:
        session.exec(text(f"ALTER SEQUENCE invoice_id_seq RESTART WITH {max_id + 1}"))  # type: ignore
        session.commit()

    print(f"Invoices — inserted: {inserted}, updated: {updated}, skipped: {skipped}")


if __name__ == "__main__":
    with Session(engine) as session:
        import_assets(session)
        import_work_orders(session)
        import_purchase_orders(session)
        import_invoices(session)
