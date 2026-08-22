"""Generates a clean, printable single-work-order view as a browser-readable
HTML page (same toolbar/print-stylesheet convention as the weekly report)."""

from sqlmodel import Session, select

from schema.models import Asset, Location, Part, Supplier, WorkOrder, WorkOrderPart
from utils.html_report_helpers import badge, card, fmt_date, fmt_money, print_page_shell, table, val

_STATUS_COLORS = {
    "requested": "blue", "scheduled": "blue", "in_progress": "amber", "awaiting_parts": "amber",
    "awaiting_po": "amber", "on_hold": "slate", "cancelled": "red", "completed": "green", "closed": "green",
}
_PRIORITY_COLORS = {"High": "red", "Medium": "amber", "Low": "slate"}


def _info_grid(pairs: list[tuple[str, str]]) -> str:
    cells = "".join(
        f'<div><div style="font-size:11px;color:#94a3b8;margin-bottom:2px">{label}</div>'
        f'<div style="font-size:13px;color:#1e293b;font-weight:600">{value}</div></div>'
        for label, value in pairs
    )
    return f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px 20px">{cells}</div>'


def generate_work_order_print_html(session: Session, work_order_id: int) -> str:
    wo = session.get(WorkOrder, work_order_id)
    if wo is None:
        raise ValueError(f"Work order {work_order_id} not found")

    asset = session.get(Asset, wo.asset_id) if wo.asset_id else None
    supplier = session.get(Supplier, wo.supplier_id) if wo.supplier_id else None
    location = session.get(Location, asset.location_id) if asset and asset.location_id else None
    parts = session.exec(
        select(WorkOrderPart).where(WorkOrderPart.work_order_id == work_order_id)
    ).all()
    part_names: dict[str, str] = {}
    for p in parts:
        if p.part_no and p.part_no not in part_names:
            part = session.get(Part, p.part_no)
            part_names[p.part_no] = part.part_name if part else p.part_no

    status = val(wo.status)
    priority = wo.priority or ""

    header_meta = (
        f'<p>WO-{wo.work_order_id}{" — " + wo.description[:80] if wo.description else ""}</p>'
        f'<div class="period">Issued {fmt_date(wo.issue_date)}</div>'
    )

    # ── Overview card ────────────────────────────────────────────
    overview = _info_grid([
        ("Asset", f'{wo.asset_id or "—"}{" — " + asset.alias if asset and asset.alias else ""}'),
        ("Manufacturer / Model", f'{asset.manufacturer if asset else "—"}{" " + asset.model_no if asset and asset.model_no else ""}'),
        ("Location", location.name if location else "—"),
        ("Type", (val(wo.typ) or "—").replace("_", " ").title()),
        ("Priority", badge(priority, _PRIORITY_COLORS.get(priority, "slate")) if priority else "—"),
        ("Status", badge(status.replace("_", " ").title(), _STATUS_COLORS.get(status, "slate")) if status else "—"),
        ("Planned / Unplanned", "Planned" if wo.planned else "Unplanned" if wo.planned is not None else "—"),
        ("Supplier", supplier.name if supplier else "—"),
        ("Supplier Contact", f'{supplier.primary_contact}{" — " + supplier.contact_number if supplier.contact_number else ""}' if supplier else "—"),
    ])
    overview_card = card("Work Order Overview", overview, "🔧")

    # ── Dates & effort card ──────────────────────────────────────
    dates = _info_grid([
        ("Issue Date", fmt_date(wo.issue_date)),
        ("Expected Date", fmt_date(wo.expected_date)),
        ("Date Completed", fmt_date(wo.date_completed)),
        ("Estimated Hours", f"{wo.estimated_hours:.1f}h" if wo.estimated_hours is not None else "—"),
        ("Actual Hours", f"{wo.actual_hours:.1f}h" if wo.actual_hours is not None else "—"),
        ("", ""),
        ("Estimated Cost", fmt_money(wo.estimated_cost)),
        ("Actual Cost", fmt_money(wo.actual_cost)),
        ("", ""),
    ])
    dates_card = card("Dates, Hours &amp; Cost", dates, "📅")

    # ── Description card ─────────────────────────────────────────
    desc_html = f'<p style="font-size:13px;color:#334155;white-space:pre-wrap">{wo.description or "—"}</p>'
    description_card = card("Description of Work", desc_html, "📝")

    # ── Parts used card ──────────────────────────────────────────
    parts_rows = [
        [
            p.part_no or "—",
            part_names.get(p.part_no, "—") if p.part_no else "—",
            str(p.quantity_used),
            fmt_money(p.unit_cost),
            fmt_money(p.total_cost),
        ]
        for p in parts
    ]
    parts_total = sum(p.total_cost or 0 for p in parts)
    parts_table = table(["Part No", "Description", "Qty", "Unit Cost", "Total"], parts_rows)
    parts_footer = (
        f'<p style="text-align:right;font-size:13px;font-weight:700;color:#1e293b;margin-top:10px">'
        f'Parts Total: {fmt_money(parts_total)}</p>' if parts_rows else ""
    )
    parts_card = card(f"Parts Used ({len(parts_rows)})", parts_table + parts_footer, "🧩")

    # ── Notes card ───────────────────────────────────────────────
    notes_html = f'<p style="font-size:13px;color:#334155;white-space:pre-wrap">{wo.notes or "—"}</p>'
    notes_card = card("Notes", notes_html, "🗒")

    # ── Sign-off card (blank, for a physical/printed copy) ───────
    signoff = (
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:32px;margin-top:8px">'
        '<div><div style="border-bottom:1px solid #cbd5e1;height:40px"></div>'
        '<p style="font-size:11px;color:#94a3b8;margin-top:4px">Technician Signature / Date</p></div>'
        '<div><div style="border-bottom:1px solid #cbd5e1;height:40px"></div>'
        '<p style="font-size:11px;color:#94a3b8;margin-top:4px">Supervisor Signature / Date</p></div>'
        '</div>'
    )
    signoff_card = card("Sign-off", signoff, "✍")

    body = overview_card + dates_card + description_card + parts_card + notes_card + signoff_card

    return print_page_shell(
        title=f"Work Order WO-{wo.work_order_id}",
        subtitle="Work Order",
        header_title=f"Work Order WO-{wo.work_order_id}",
        header_meta=header_meta,
        body=body,
    )
