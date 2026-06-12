"""
Import data from spreadsheets in data_files/ into the database.

Usage:
    uv run python data_imports.py
"""

from datetime import date
from pathlib import Path

import openpyxl

from schema.database import engine
from schema.models import Asset, AssetCategory, AssetOwnership, AssetStatus, AssetSubStatus
from sqlmodel import Session


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


if __name__ == "__main__":
    with Session(engine) as session:
        import_assets(session)
