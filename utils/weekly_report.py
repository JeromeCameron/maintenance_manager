"""Generates the weekly maintenance management PDF report."""

import io
from calendar import monthrange
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlmodel import Session, select

from crud.utility import get_holidays as _get_holidays
from schema.models import (
    Asset,
    AssetModel,
    AssetPM,
    Budget,
    CommodityRate,
    Downtime,
    Invoice,
    Issue,
    IssueStatus,
    WorkOrder,
    WorkOrderStatus,
)
from utils.down_hours import get_production_downtime_hours

# ── Palette ────────────────────────────────────────────────────────────────────
_BLUE  = "#2563eb"
_SLATE = "#64748b"
_GREEN = "#16a34a"
_AMBER = "#d97706"
_RED   = "#dc2626"
_LIGHT = "#f8fafc"
_BORDER = "#e2e8f0"

RL_BLUE   = colors.HexColor(_BLUE)
RL_SLATE  = colors.HexColor(_SLATE)
RL_LIGHT  = colors.HexColor(_LIGHT)
RL_BORDER = colors.HexColor(_BORDER)
RL_GREEN  = colors.HexColor(_GREEN)
RL_AMBER  = colors.HexColor(_AMBER)
RL_RED    = colors.HexColor(_RED)
RL_WHITE  = colors.white
RL_DARK   = colors.HexColor("#1e293b")


# ── Date helpers ───────────────────────────────────────────────────────────────
class WeekRange:
    def __init__(self, start: date, end: date):
        self.start = start
        self.end = end

    def label(self) -> str:
        return f"{self.start.strftime('%d %b %Y')} – {self.end.strftime('%d %b %Y')}"

    def contains(self, v) -> bool:
        d = _to_date(v)
        return d is not None and self.start <= d <= self.end


def _to_date(v) -> Optional[date]:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return date.fromisoformat(v[:10])
        except ValueError:
            return None
    return None


def _in_range(v, start: date, end: date) -> bool:
    d = _to_date(v)
    return d is not None and start <= d <= end


def _prev_week() -> WeekRange:
    today = date.today()
    last_sun = today - timedelta(days=today.weekday() + 1)
    last_mon = last_sun - timedelta(days=6)
    return WeekRange(last_mon, last_sun)


def _current_month() -> tuple[date, date]:
    today = date.today()
    start = today.replace(day=1)
    end = (date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)) - timedelta(days=1)
    return start, end


def _prev_month() -> tuple[date, date]:
    end = date.today().replace(day=1) - timedelta(days=1)
    return end.replace(day=1), end


# ── Formatters ─────────────────────────────────────────────────────────────────
def _fmt_date(v) -> str:
    d = _to_date(v)
    return d.strftime("%d-%b-%y") if d else "—"


def _fmt_hrs(v) -> str:
    return f"{v:.1f}" if v is not None else "—"


def _fmt_money(v) -> str:
    if v is None:
        return "—"
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"${v / 1_000:.1f}k"
    return f"${v:.0f}"


# ── Table style ────────────────────────────────────────────────────────────────
_BASE_TABLE = TableStyle([
    ("BACKGROUND",    (0, 0), (-1, 0),  RL_BLUE),
    ("TEXTCOLOR",     (0, 0), (-1, 0),  RL_WHITE),
    ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
    ("FONTSIZE",      (0, 0), (-1, 0),  7),
    ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
    ("FONTSIZE",      (0, 1), (-1, -1), 7),
    ("ROWBACKGROUNDS",(0, 1), (-1, -1), [RL_WHITE, RL_LIGHT]),
    ("GRID",          (0, 0), (-1, -1), 0.25, RL_BORDER),
    ("ALIGN",         (0, 0), (-1, -1), "LEFT"),
    ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING",   (0, 0), (-1, -1), 4),
    ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ("TOPPADDING",    (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
])


def _make_table(headers, rows, col_widths=None, extra=None) -> Table:
    style = TableStyle(_BASE_TABLE.getCommands())
    if extra:
        for cmd in extra:
            style.add(*cmd)
    t = Table([headers] + rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(style)
    return t


# ── Styles ─────────────────────────────────────────────────────────────────────
def _styles():
    return {
        "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=18, textColor=RL_BLUE, spaceAfter=2),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10, textColor=RL_BLUE, spaceBefore=10, spaceAfter=5),
        "h3": ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=8,  textColor=RL_DARK, spaceBefore=6, spaceAfter=3),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=8, textColor=RL_DARK, spaceAfter=2),
        "small": ParagraphStyle("small", fontName="Helvetica", fontSize=7, textColor=RL_SLATE),
        "kpi_v": ParagraphStyle("kpi_v", fontName="Helvetica-Bold", fontSize=18, textColor=RL_BLUE, alignment=TA_CENTER),
        "kpi_l": ParagraphStyle("kpi_l", fontName="Helvetica", fontSize=7, textColor=RL_SLATE, alignment=TA_CENTER),
        "sub": ParagraphStyle("sub", fontName="Helvetica", fontSize=9, textColor=RL_SLATE, spaceAfter=2),
    }


# ── Chart helpers ──────────────────────────────────────────────────────────────
def _to_img(fig, w_cm=15, h_cm=5) -> Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=w_cm * cm, height=h_cm * cm)


def _hbar_chart(labels, values, title, color=_BLUE, xlabel="Hours"):
    n = max(len(labels), 1)
    fig, ax = plt.subplots(figsize=(9, max(2.5, n * 0.45 + 1)))
    y = range(n)
    bars = ax.barh(list(y), values, color=color, height=0.55)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel(xlabel, fontsize=8)
    ax.set_title(title, fontsize=9, fontweight="bold", pad=5)
    ax.xaxis.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    mx = max(values) if values else 1
    for bar, val in zip(bars, values):
        if val > 0:
            ax.text(bar.get_width() + mx * 0.01, bar.get_y() + bar.get_height() / 2, f"{val:.1f}", va="center", fontsize=7)
    plt.tight_layout()
    return fig


def _grouped_bar(labels, series_vals, series_names, title, ylabel="Hours", palette=None):
    palette = palette or [_BLUE, _AMBER, _GREEN, _RED]
    n = len(labels)
    ns = len(series_vals)
    fig, ax = plt.subplots(figsize=(10, max(3.5, n * 0.3 + 2)))
    x = np.arange(n)
    w = 0.75 / ns
    for i, (vals, name, col) in enumerate(zip(series_vals, series_names, palette)):
        ax.bar(x + (i - ns / 2 + 0.5) * w, vals, w * 0.9, label=name, color=col, alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8, rotation=20, ha="right")
    ax.set_ylabel(ylabel, fontsize=8)
    ax.set_title(title, fontsize=9, fontweight="bold", pad=5)
    ax.yaxis.grid(True, alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)
    ax.legend(fontsize=7)
    plt.tight_layout()
    return fig


def _pie_chart(labels, values, title):
    palette = [_BLUE, _AMBER, _GREEN, _RED, _SLATE, "#8b5cf6", "#06b6d4"]
    pairs = [(l, v) for l, v in zip(labels, values) if v > 0]
    fig, ax = plt.subplots(figsize=(5, 4))
    if pairs:
        lbs, vals = zip(*pairs)
        wedges, _, autotexts = ax.pie(vals, labels=None, autopct="%1.0f%%",
                                       colors=palette[:len(vals)], startangle=90, pctdistance=0.78)
        for t in autotexts:
            t.set_fontsize(7)
        ax.legend(lbs, loc="lower center", bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=7)
    else:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes, fontsize=9)
    ax.set_title(title, fontsize=9, fontweight="bold", pad=5)
    plt.tight_layout()
    return fig


# ── Data gathering ─────────────────────────────────────────────────────────────
def _hours_in_range(
    all_dts: list,
    holidays: set,
    range_start: date,
    range_end: date,
) -> float:
    """Sum shift-aware production downtime hours for events overlapping [range_start, range_end]."""
    total = 0.0
    for dt in all_dts:
        if dt.start_date is None or dt.start_time is None:
            continue
        event_end_date = dt.end_date or date.today()
        event_end_time = dt.end_time or datetime.now().time()
        if dt.start_date > range_end or event_end_date < range_start:
            continue
        seg_start_date = max(dt.start_date, range_start)
        seg_start_time = dt.start_time if dt.start_date >= range_start else time(0, 0)
        seg_end_date = min(event_end_date, range_end)
        seg_end_time = event_end_time if event_end_date <= range_end else time(23, 59, 59)
        total += get_production_downtime_hours(
            seg_start_date, seg_start_time, holidays,
            seg_end_date, seg_end_time, dt.shift_asset,
        )
    return round(total, 2)


def _gather(session: Session) -> dict:
    week = _prev_week()
    m_s, m_e = _current_month()
    p_s, p_e = _prev_month()
    today = date.today()

    assets      = list(session.exec(select(Asset)).all())
    models      = list(session.exec(select(AssetModel)).all())
    downtimes   = list(session.exec(select(Downtime)).all())
    work_orders = list(session.exec(select(WorkOrder)).all())
    issues      = list(session.exec(select(Issue)).all())
    budgets     = list(session.exec(select(Budget)).all())
    invoices    = list(session.exec(select(Invoice)).all())
    asset_pms   = list(session.exec(select(AssetPM)).all())
    rates       = list(session.exec(select(CommodityRate).order_by(CommodityRate.effective_date.desc())).all())
    holidays    = {h.holiday_date for h in _get_holidays(session)}

    model_map = {m.model_no: m for m in models}
    asset_model_map = {a.asset_id: model_map.get(a.model_no) for a in assets if a.model_no}

    def rate_at(v) -> float:
        d = _to_date(v)
        if not d or not rates:
            return 0
        ds = d.isoformat()
        for r in rates:
            if r.effective_date.isoformat() <= ds:
                return r.rate_per_lb
        return 0

    def calc_bales(range_start: date, range_end: date):
        bales, value = 0.0, 0.0
        for dt in downtimes:
            if not dt.asset_id or dt.start_date is None or dt.start_time is None:
                continue
            event_end = dt.end_date or today
            if dt.start_date > range_end or event_end < range_start:
                continue
            m = asset_model_map.get(dt.asset_id)
            if not m or not m.bale_time or not m.bale_weight:
                continue
            hrs = _hours_in_range([dt], holidays, range_start, range_end)
            lost = hrs * (60 / m.bale_time)
            bales += lost
            value += lost * m.bale_weight * rate_at(dt.start_date)
        return round(bales), value

    open_statuses = {WorkOrderStatus.requested, WorkOrderStatus.scheduled,
                     WorkOrderStatus.awaiting_parts, WorkOrderStatus.awaiting_po,
                     WorkOrderStatus.in_progress, WorkOrderStatus.on_hold}

    # Like-for-like: compare current month up to today vs same day-of-month in previous month
    prev_like_day = min(today.day, monthrange(p_s.year, p_s.month)[1])
    prev_like_end = date(p_s.year, p_s.month, prev_like_day)

    week_dts  = [d for d in downtimes   if week.contains(d.start_date or d.log_date)]
    month_dts = [d for d in downtimes   if _in_range(d.start_date or d.log_date, m_s, m_e)]
    prev_dts  = [d for d in downtimes   if _in_range(d.start_date or d.log_date, p_s, p_e)]
    week_wos  = [w for w in work_orders if week.contains(w.issue_date) or week.contains(w.date_completed)]
    open_wos  = [w for w in work_orders if w.status in open_statuses]
    month_inv = [i for i in invoices    if _in_range(i.rec_date or i.job_date, m_s, m_e)]
    month_bud = [b for b in budgets     if _in_range(b.month, m_s, m_e)]
    prev_bud  = [b for b in budgets     if _in_range(b.month, p_s, p_e)]
    prev_inv  = [i for i in invoices    if _in_range(i.rec_date or i.job_date, p_s, p_e)]
    open_iss  = [i for i in issues      if i.status in (IssueStatus.open, IssueStatus.in_review)]
    week_iss  = [i for i in issues      if week.contains(_to_date(i.reported_at))]
    overdue_pms  = [p for p in asset_pms if p.active and p.next_service and _to_date(p.next_service) < today]
    due_soon_pms = [p for p in asset_pms if p.active and p.next_service and today <= _to_date(p.next_service) <= today + timedelta(days=14)]

    # Properly attributed monthly hours (shift-aware, split across month boundaries)
    curr_month_hrs = _hours_in_range(downtimes, holidays, m_s, today)
    prev_like_hrs  = _hours_in_range(downtimes, holidays, p_s, prev_like_end)

    # Per-asset breakdown for the comparison chart
    curr_by_asset: dict[str, float] = defaultdict(float)
    prev_like_by_asset: dict[str, float] = defaultdict(float)
    for dt in downtimes:
        if not dt.asset_id or dt.start_date is None or dt.start_time is None:
            continue
        event_end = dt.end_date or today
        if not (dt.start_date > today or event_end < m_s):
            curr_by_asset[dt.asset_id] += _hours_in_range([dt], holidays, m_s, today)
        if not (dt.start_date > prev_like_end or event_end < p_s):
            prev_like_by_asset[dt.asset_id] += _hours_in_range([dt], holidays, p_s, prev_like_end)

    return dict(
        week=week, m_s=m_s, m_e=m_e, p_s=p_s, p_e=p_e, today=today,
        assets=assets, asset_model_map=asset_model_map,
        week_dts=week_dts, month_dts=month_dts, prev_dts=prev_dts,
        week_wos=week_wos, open_wos=open_wos,
        month_inv=month_inv, month_bud=month_bud, prev_bud=prev_bud, prev_inv=prev_inv,
        open_iss=open_iss, week_iss=week_iss,
        asset_pms=asset_pms, overdue_pms=overdue_pms, due_soon_pms=due_soon_pms,
        curr_month_hrs=curr_month_hrs,
        prev_like_hrs=prev_like_hrs,
        prev_like_end=prev_like_end,
        curr_by_asset=dict(curr_by_asset),
        prev_like_by_asset=dict(prev_like_by_asset),
        week_bales=calc_bales(week.start, week.end),
        month_bales=calc_bales(m_s, today),
    )


# ── Section builders ───────────────────────────────────────────────────────────
def _sec_assets(d, S, W):
    assets = d["assets"]
    status_count = Counter(str(a.status) for a in assets)
    statuses = [("operational", "Operational", RL_GREEN, colors.HexColor("#dcfce7"), colors.HexColor(_GREEN)),
                ("maintenance", "Maintenance",  RL_AMBER, colors.HexColor("#fef3c7"), colors.HexColor(_AMBER)),
                ("out_of_service", "Out of Service", RL_RED, colors.HexColor("#fee2e2"), colors.HexColor(_RED))]

    kpi_rows = [[], []]
    for st, lbl, tc, bg, border in statuses:
        cnt = status_count.get(st, 0)
        kpi_rows[0].append(Paragraph(str(cnt), S["kpi_v"]))
        kpi_rows[1].append(Paragraph(lbl, S["kpi_l"]))

    kpi = Table(kpi_rows, colWidths=[W / 3] * 3)
    kpi_style = TableStyle([
        ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",     (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 8),
    ])
    for i, (_, _, tc, bg, border) in enumerate(statuses):
        kpi_style.add("BACKGROUND", (i, 0), (i, 1), bg)
        kpi_style.add("BOX",        (i, 0), (i, 1), 0.75, border)
    kpi.setStyle(kpi_style)

    rows = []
    extra = []
    sev_map = {"operational": _GREEN, "maintenance": _AMBER, "out_of_service": _RED}
    for i, a in enumerate(sorted(assets, key=lambda x: x.asset_id or "")):
        st = str(a.status) if a.status else ""
        rows.append([
            a.asset_id or "—",
            a.alias or "—",
            str(a.category or "—").replace("_", " ").title(),
            str(a.status or "—").replace("_", " ").title(),
            str(a.sub_status or "—").replace("_", " ").title() if a.sub_status else "—",
        ])
        c = sev_map.get(st)
        if c:
            extra.append(("TEXTCOLOR", (3, i + 1), (3, i + 1), colors.HexColor(c)))

    cw = [W * f for f in (0.15, 0.25, 0.2, 0.2, 0.2)]
    return [
        Paragraph("1. Asset Summary", S["h2"]),
        kpi,
        Spacer(1, 8),
        _make_table(["Asset ID", "Alias", "Category", "Status", "Sub-Status"], rows, cw, extra) if rows
        else Paragraph("No assets on record.", S["small"]),
    ]


def _sec_downtime_week(d, S, W):
    week_dts = d["week_dts"]
    week: WeekRange = d["week"]
    total_hrs = sum(dt.downtime_hours or 0 for dt in week_dts)

    elems = [Paragraph(f"2. Downtime – Previous Week ({week.label()})", S["h2"])]
    elems.append(Paragraph(
        f"<b>{len(week_dts)}</b> event(s) &nbsp;|&nbsp; <b>{total_hrs:.1f} h</b> production hours lost",
        S["body"]
    ))
    elems.append(Spacer(1, 5))

    if week_dts:
        rows = [[
            dt.asset_id or "—",
            _fmt_date(dt.start_date),
            _fmt_date(dt.end_date),
            _fmt_hrs(dt.downtime_hours),
            "Yes" if dt.planned else "No",
            str(dt.component_affected or "—")[:30],
            str(dt.details or "—")[:35],
        ] for dt in sorted(week_dts, key=lambda x: str(x.start_date or ""))]
        cw = [W * f for f in (0.1, 0.1, 0.1, 0.07, 0.07, 0.22, 0.34)]
        elems.append(_make_table(
            ["Asset", "Start", "End", "Hours", "Planned", "Component", "Details"], rows, cw
        ))
        elems.append(Spacer(1, 6))

        by_asset: dict[str, float] = defaultdict(float)
        for dt in week_dts:
            if dt.asset_id:
                by_asset[dt.asset_id] += dt.downtime_hours or 0
        if by_asset:
            labels, vals = zip(*sorted(by_asset.items(), key=lambda x: -x[1]))
            fig = _hbar_chart(list(labels), list(vals), "Downtime Hours by Asset – Previous Week", _RED)
            h = max(4, len(labels) * 0.55 + 1.5)
            elems.append(_to_img(fig, 15, h))
    else:
        elems.append(Paragraph("No downtime recorded in the previous week.", S["small"]))

    return elems


def _sec_downtime_month(d, S, W):
    month_dts, prev_dts = d["month_dts"], d["prev_dts"]
    m_s, p_s = d["m_s"], d["p_s"]
    curr_hrs = sum(dt.downtime_hours or 0 for dt in month_dts)
    prev_hrs = sum(dt.downtime_hours or 0 for dt in prev_dts)
    delta = curr_hrs - prev_hrs

    elems = [Paragraph("3. Downtime – Month to Date & Comparison", S["h2"])]
    delta_tag = f"+{delta:.1f}h" if delta >= 0 else f"{delta:.1f}h"
    elems.append(Paragraph(
        f"<b>{m_s.strftime('%b %Y')}</b>: {curr_hrs:.1f} h &nbsp;|&nbsp; "
        f"<b>{p_s.strftime('%b %Y')}</b>: {prev_hrs:.1f} h &nbsp;|&nbsp; Change: <b>{delta_tag}</b>",
        S["body"]
    ))
    elems.append(Spacer(1, 5))

    curr_by: dict[str, float] = defaultdict(float)
    prev_by: dict[str, float] = defaultdict(float)
    for dt in month_dts:
        if dt.asset_id:
            curr_by[dt.asset_id] += dt.downtime_hours or 0
    for dt in prev_dts:
        if dt.asset_id:
            prev_by[dt.asset_id] += dt.downtime_hours or 0

    all_ids = sorted(set(curr_by) | set(prev_by))
    if all_ids:
        fig = _grouped_bar(
            all_ids,
            [[prev_by.get(a, 0) for a in all_ids], [curr_by.get(a, 0) for a in all_ids]],
            [p_s.strftime("%b %y"), m_s.strftime("%b %y")],
            "Downtime Comparison by Asset (Hours)",
            palette=[_SLATE, _BLUE],
        )
        elems.append(_to_img(fig, 16, 5))
    else:
        elems.append(Paragraph("No downtime data to compare.", S["small"]))

    return elems


def _sec_bales(d, S, W):
    wb, wv = d["week_bales"]
    mb, mv = d["month_bales"]
    elems = [Paragraph("4. Bales Lost & Estimated Cost", S["h2"])]
    rows = [
        ["Previous Week",   f"{wb:,}", f"${wv:,.2f}"],
        ["Month to Date",   f"{mb:,}", f"${mv:,.2f}"],
    ]
    cw = [W * 0.4, W * 0.3, W * 0.3]
    elems.append(_make_table(["Period", "Bales Lost", "Est. Value (USD)"], rows, cw))
    elems.append(Paragraph("Calculated from downtime hours × bale rate × commodity price (USD/lb).", S["small"]))
    return elems


def _sec_work_orders(d, S, W):
    week_wos, open_wos = d["week_wos"], d["open_wos"]
    week: WeekRange = d["week"]
    started   = [w for w in week_wos if week.contains(w.issue_date)]
    completed = [w for w in week_wos if week.contains(w.date_completed)]

    elems = [Paragraph("5. Work Orders – Previous Week", S["h2"])]
    elems.append(Paragraph(
        f"<b>{len(started)}</b> started &nbsp;|&nbsp; <b>{len(completed)}</b> completed",
        S["body"]
    ))
    elems.append(Spacer(1, 5))

    if week_wos:
        rows = [[
            str(w.work_order_id or "—"),
            w.asset_id or "—",
            str(w.typ or "—").replace("_", " ").title(),
            str(w.priority or "—").title(),
            str(w.status or "—").replace("_", " ").title() if w.status else "—",
            _fmt_date(w.issue_date),
            _fmt_date(w.date_completed),
            str(w.description or "—")[:40],
        ] for w in sorted(week_wos, key=lambda x: str(x.issue_date or ""))]
        cw = [W * f for f in (0.06, 0.1, 0.1, 0.08, 0.12, 0.09, 0.09, 0.36)]
        elems.append(_make_table(
            ["WO #", "Asset", "Type", "Priority", "Status", "Issued", "Completed", "Description"],
            rows, cw
        ))
    else:
        elems.append(Paragraph("No work orders started or completed in the previous week.", S["small"]))

    elems.append(Spacer(1, 8))
    elems.append(Paragraph(f"5b. Open Work Orders ({len(open_wos)} total)", S["h2"]))

    status_counts = Counter(str(w.status) for w in open_wos)
    if status_counts:
        lbs = [s.replace("_", " ").title() for s in status_counts]
        vals = list(status_counts.values())
        fig = _pie_chart(lbs, vals, "Open Work Orders by Status")

        tbl_rows = [[s.replace("_", " ").title(), str(c)]
                    for s, c in sorted(status_counts.items(), key=lambda x: -x[1])]
        tbl = _make_table(["Status", "Count"], tbl_rows, [W * 0.6, W * 0.4])

        img = _to_img(fig, 7, 5)
        side = Table([[img, tbl]], colWidths=[7.5 * cm, W - 7.5 * cm])
        side.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        elems.append(side)
    else:
        elems.append(Paragraph("No open work orders.", S["small"]))

    return elems


def _sec_pm(d, S, W):
    overdue, due_soon, total = d["overdue_pms"], d["due_soon_pms"], len(d["asset_pms"])
    active_total = len([p for p in d["asset_pms"] if p.active])
    pct = ((active_total - len(overdue)) / active_total * 100) if active_total else 0
    today = d["today"]

    elems = [Paragraph("6. PM Compliance", S["h2"])]
    elems.append(Paragraph(
        f"Active PMs: <b>{active_total}</b> &nbsp;|&nbsp; "
        f"Overdue: <b>{len(overdue)}</b> &nbsp;|&nbsp; "
        f"Due within 14 days: <b>{len(due_soon)}</b> &nbsp;|&nbsp; "
        f"Compliance: <b>{pct:.0f}%</b>",
        S["body"]
    ))
    elems.append(Spacer(1, 5))

    if overdue:
        rows, extra = [], []
        for i, p in enumerate(sorted(overdue, key=lambda x: _to_date(x.next_service) or date.max)):
            ns = _to_date(p.next_service)
            days_od = (today - ns).days if ns else "—"
            rows.append([str(p.id), p.asset_id or "—", p.pm_plan_id or "—",
                         _fmt_date(p.last_service), _fmt_date(p.next_service), str(days_od)])
            extra.append(("TEXTCOLOR", (5, i + 1), (5, i + 1), RL_RED))
        cw = [W * f for f in (0.08, 0.15, 0.22, 0.18, 0.18, 0.19)]
        elems.append(_make_table(["PM ID", "Asset", "Plan", "Last Service", "Next Service", "Days Overdue"],
                                 rows, cw, extra))
    else:
        elems.append(Paragraph("No overdue PMs — fully compliant.", S["small"]))

    return elems


def _sec_finance(d, S, W):
    month_bud, month_inv = d["month_bud"], d["month_inv"]
    prev_bud, prev_inv   = d["prev_bud"],  d["prev_inv"]
    m_s, p_s             = d["m_s"],       d["p_s"]

    total_bud = sum(b.amount for b in month_bud)
    total_act = sum(i.subtotal for i in month_inv)
    prev_bud_t = sum(b.amount for b in prev_bud)
    prev_act_t = sum(i.subtotal for i in prev_inv)

    elems = [Paragraph("7. Finance – Spend vs Budget", S["h2"])]
    elems.append(Paragraph(
        f"<b>{m_s.strftime('%B %Y')}</b>: "
        f"Budget {_fmt_money(total_bud)} | Actual {_fmt_money(total_act)} | "
        f"Variance {_fmt_money(total_bud - total_act)}",
        S["body"]
    ))
    elems.append(Spacer(1, 5))

    bud_by_gl: dict[str, float] = defaultdict(float)
    for b in month_bud:
        if b.gl_code:
            bud_by_gl[b.gl_code] += b.amount

    if bud_by_gl:
        gl_labels = sorted(bud_by_gl, key=lambda g: -bud_by_gl[g])
        fig = _hbar_chart(
            [g[:25] for g in gl_labels],
            [bud_by_gl[g] for g in gl_labels],
            f"Budget by GL Code – {m_s.strftime('%B %Y')}",
            _BLUE, "Amount ($)"
        )
        h = max(4, len(gl_labels) * 0.5 + 1.5)
        elems.append(_to_img(fig, 15, h))

    rows = [
        [m_s.strftime("%B %Y"), _fmt_money(total_bud), _fmt_money(total_act),
         _fmt_money(total_bud - total_act),
         f"{total_act / total_bud * 100:.1f}%" if total_bud else "—"],
        [p_s.strftime("%B %Y"), _fmt_money(prev_bud_t), _fmt_money(prev_act_t),
         _fmt_money(prev_bud_t - prev_act_t),
         f"{prev_act_t / prev_bud_t * 100:.1f}%" if prev_bud_t else "—"],
    ]
    cw = [W * 0.22, W * 0.2, W * 0.2, W * 0.2, W * 0.18]
    elems.append(Spacer(1, 6))
    elems.append(_make_table(["Period", "Budget", "Actual", "Variance", "Utilisation"], rows, cw))
    return elems


def _sec_issues(d, S, W):
    open_iss, week_iss = d["open_iss"], d["week_iss"]
    sev_color = {"critical": _RED, "high": _AMBER, "medium": _BLUE, "low": _SLATE}

    elems = [Paragraph("8. Issues", S["h2"])]
    elems.append(Paragraph(
        f"Open: <b>{len(open_iss)}</b> &nbsp;|&nbsp; New this week: <b>{len(week_iss)}</b>",
        S["body"]
    ))
    elems.append(Spacer(1, 5))

    if open_iss:
        rows, extra = [], []
        for i, iss in enumerate(sorted(open_iss, key=lambda x: str(x.reported_at or ""), reverse=True)):
            rows.append([
                str(iss.id),
                iss.asset_id or "—",
                str(iss.severity or "—").title(),
                str(iss.status or "—").replace("_", " ").title() if iss.status else "—",
                _fmt_date(_to_date(iss.reported_at)),
                str(iss.description or "—")[:50],
            ])
            c = sev_color.get(str(iss.severity) if iss.severity else "", _SLATE)
            extra.append(("TEXTCOLOR", (2, i + 1), (2, i + 1), colors.HexColor(c)))
        cw = [W * f for f in (0.06, 0.1, 0.1, 0.14, 0.1, 0.5)]
        elems.append(_make_table(["ID", "Asset", "Severity", "Status", "Reported", "Description"],
                                 rows, cw, extra))
    else:
        elems.append(Paragraph("No open issues.", S["small"]))

    return elems


def _sec_reliability(d, S, W):
    month_dts, assets = d["month_dts"], d["assets"]
    m_s, p_s = d["m_s"], d["p_s"]
    prev_dts = d["prev_dts"]

    WORKING_HRS = 8 * 22  # ~22 working days × 8h

    def metrics(dts):
        by_asset: dict[str, list[float]] = defaultdict(list)
        for dt in dts:
            if dt.asset_id and dt.downtime_hours:
                by_asset[dt.asset_id].append(dt.downtime_hours)
        result = {}
        for a in assets:
            events = by_asset.get(a.asset_id, [])
            n = len(events)
            dt_hrs = sum(events)
            result[a.asset_id] = {
                "alias": a.alias or "",
                "n": n,
                "dt_hrs": dt_hrs,
                "avail": max(0, (WORKING_HRS - dt_hrs) / WORKING_HRS * 100),
                "mttr": dt_hrs / n if n else None,
                "mtbf": (WORKING_HRS - dt_hrs) / n if n else None,
            }
        return result

    curr_m = metrics(month_dts)
    rows, extra = [], []
    for i, a in enumerate(sorted(assets, key=lambda x: x.asset_id or "")):
        r = curr_m[a.asset_id]
        rows.append([
            a.asset_id or "—", r["alias"] or "—",
            str(r["n"]),
            _fmt_hrs(r["dt_hrs"]),
            _fmt_hrs(r["mttr"]) if r["mttr"] is not None else "—",
            _fmt_hrs(r["mtbf"]) if r["mtbf"] is not None else "—",
            f"{r['avail']:.1f}%",
        ])
        c = _GREEN if r["avail"] >= 90 else _AMBER if r["avail"] >= 75 else _RED
        extra.append(("TEXTCOLOR", (6, i + 1), (6, i + 1), colors.HexColor(c)))

    cw = [W * f for f in (0.13, 0.16, 0.09, 0.12, 0.1, 0.1, 0.1)]
    cw[-1] = W - sum(cw[:-1])

    elems = [Paragraph("9. Reliability Summary", S["h2"])]
    elems.append(Paragraph(f"Month to date: {m_s.strftime('%B %Y')}  (based on ~{WORKING_HRS}h scheduled hours)", S["body"]))
    elems.append(Spacer(1, 5))
    if rows:
        elems.append(_make_table(
            ["Asset", "Alias", "Failures", "DT Hrs", "MTTR (h)", "MTBF (h)", "Availability"],
            rows, cw, extra
        ))
    else:
        elems.append(Paragraph("No data available.", S["small"]))

    # Availability bar chart
    avail_data = [(a.asset_id, curr_m[a.asset_id]["avail"]) for a in assets if a.asset_id]
    if avail_data:
        lbs, vals = zip(*sorted(avail_data, key=lambda x: x[1]))
        bar_colors = [_GREEN if v >= 90 else _AMBER if v >= 75 else _RED for v in vals]
        fig, ax = plt.subplots(figsize=(9, max(2.5, len(lbs) * 0.45 + 1)))
        y = range(len(lbs))
        ax.barh(list(y), list(vals), color=bar_colors, height=0.55)
        ax.axvline(x=90, color=_GREEN, linestyle="--", linewidth=0.8, label="90% target")
        ax.set_yticks(list(y))
        ax.set_yticklabels(lbs, fontsize=8)
        ax.set_xlabel("Availability (%)", fontsize=8)
        ax.set_title("Asset Availability – Month to Date", fontsize=9, fontweight="bold", pad=5)
        ax.set_xlim(0, 105)
        ax.xaxis.grid(True, alpha=0.3, linestyle="--")
        ax.set_axisbelow(True)
        ax.legend(fontsize=7)
        for i, v in enumerate(vals):
            ax.text(v + 0.5, i, f"{v:.1f}%", va="center", fontsize=7)
        plt.tight_layout()
        elems.append(Spacer(1, 6))
        elems.append(_to_img(fig, 15, max(3.5, len(lbs) * 0.55 + 1.5)))

    return elems


# ── Page decorations ───────────────────────────────────────────────────────────
def _header_footer(canvas, doc):
    canvas.saveState()
    W_pg, H_pg = A4

    # Top bar
    canvas.setFillColor(RL_BLUE)
    canvas.rect(0, H_pg - 26, W_pg, 26, fill=True, stroke=False)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(RL_WHITE)
    canvas.drawString(18, H_pg - 17, "MAINTENANCE MANAGER")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(W_pg - 18, H_pg - 17,
                           f"Weekly Report  ·  Generated {date.today().strftime('%d %b %Y')}")

    # Bottom bar
    canvas.setFillColor(colors.HexColor(_BORDER))
    canvas.rect(0, 0, W_pg, 20, fill=True, stroke=False)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(RL_SLATE)
    canvas.drawString(18, 6, "Confidential – Internal Use Only")
    canvas.drawRightString(W_pg - 18, 6, f"Page {canvas._pageNumber}")

    canvas.restoreState()


# ── Public entry point ─────────────────────────────────────────────────────────
def generate_weekly_report(session: Session) -> bytes:
    buf = io.BytesIO()
    margin = 1.5 * cm
    W = A4[0] - 2 * margin

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=1.8 * cm, bottomMargin=1.5 * cm,
    )

    S = _styles()
    d = _gather(session)
    week: WeekRange = d["week"]

    story = [
        Paragraph("Weekly Maintenance Report", S["h1"]),
        Paragraph(f"Period: {week.label()}", S["sub"]),
        Paragraph(f"Generated: {date.today().strftime('%A, %d %B %Y')}", S["sub"]),
        HRFlowable(width="100%", thickness=1, color=RL_BLUE, spaceAfter=10),
    ]

    sections = [
        _sec_assets, _sec_downtime_week, _sec_downtime_month,
        _sec_bales, _sec_work_orders, _sec_pm,
        _sec_finance, _sec_issues, _sec_reliability,
    ]

    for i, fn in enumerate(sections):
        story.extend(fn(d, S, W))
        if i < len(sections) - 1:
            story.append(Spacer(1, 6))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()
