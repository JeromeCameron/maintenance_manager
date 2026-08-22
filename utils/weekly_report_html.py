"""Generates the weekly maintenance report as a browser-readable HTML page."""

from collections import Counter, defaultdict
from datetime import date

from sqlmodel import Session

from utils.html_report_helpers import badge as _badge
from utils.html_report_helpers import card as _card
from utils.html_report_helpers import fmt_date as _fmt_date
from utils.html_report_helpers import fmt_money as _fmt_money
from utils.html_report_helpers import print_page_shell
from utils.html_report_helpers import table as _table
from utils.html_report_helpers import val as _val
from utils.weekly_report import _gather, _to_date, WeekRange


# ── Helpers specific to this report ─────────────────────────────────────────────

def _status_badge(st: str) -> str:
    color = {"operational": "green", "maintenance": "amber", "out_of_service": "red",
             "disposed": "slate", "retired": "slate"}.get(st, "slate")
    return _badge(st.replace("_", " ").title(), color)


def _css_bar(value: float, max_val: float, color: str = "#2563eb") -> str:
    pct = min(100, (value / max_val * 100)) if max_val else 0
    label = f"{value:.1f}"
    return (
        f'<div style="display:flex;align-items:center;gap:8px">'
        f'<div style="flex:1;background:#f1f5f9;border-radius:4px;height:10px;overflow:hidden">'
        f'<div style="width:{pct:.1f}%;background:{color};height:100%;border-radius:4px"></div></div>'
        f'<span style="font-size:11px;color:#64748b;white-space:nowrap;min-width:36px;text-align:right">{label}</span>'
        f'</div>'
    )


def _kpi_row(items: list) -> str:
    """items = list of (value, label, color_key)"""
    palette = {
        "green": ("#dcfce7", "#16a34a"),
        "amber": ("#fef3c7", "#b45309"),
        "red":   ("#fee2e2", "#dc2626"),
        "blue":  ("#dbeafe", "#2563eb"),
        "slate": ("#f1f5f9", "#64748b"),
    }
    cells = ""
    for value, label, color in items:
        bg, tc = palette.get(color, palette["slate"])
        cells += (
            f'<div style="flex:1;background:{bg};border-radius:10px;padding:18px 12px;'
            f'text-align:center;border:1px solid {tc}22">'
            f'<div style="font-size:32px;font-weight:800;color:{tc};line-height:1">{value}</div>'
            f'<div style="font-size:11px;color:{tc};margin-top:6px;font-weight:500">{label}</div>'
            f'</div>'
        )
    return f'<div style="display:flex;gap:12px;margin-bottom:16px">{cells}</div>'


# ── Sections ───────────────────────────────────────────────────────────────────

def _sec_assets(d: dict) -> str:
    assets = d["assets"]
    status_count: Counter = Counter(_val(a.status) for a in assets)

    kpi = _kpi_row([
        (status_count.get("operational", 0),    "Operational",    "green"),
        (status_count.get("maintenance", 0),     "Maintenance",    "amber"),
        (status_count.get("out_of_service", 0),  "Out of Service", "red"),
        (status_count.get("disposed", 0) + status_count.get("retired", 0), "Disposed / Retired", "slate"),
    ])

    rows = []
    for a in sorted(assets, key=lambda x: x.asset_id or ""):
        st = _val(a.status)
        cat = _val(a.category).replace("_", " ").title() if a.category else "—"
        sub = _val(a.sub_status).replace("_", " ").title() if a.sub_status else "—"
        rows.append([
            f'<strong>{a.asset_id or "—"}</strong>',
            a.alias or "—",
            cat,
            _status_badge(st) if st else "—",
            sub,
        ])

    tbl = _table(["Asset ID", "Alias", "Category", "Status", "Sub-Status"], rows)
    return _card("1. Asset Summary", kpi + tbl, "▦")


def _sec_downtime_week(d: dict) -> str:
    week_dts = d["week_dts"]
    week: WeekRange = d["week"]
    total_hrs = sum(dt.downtime_hours or 0 for dt in week_dts)

    kpi = _kpi_row([
        (len(week_dts), "Events", "red"),
        (f"{total_hrs:.1f}h", "Hours Lost", "amber"),
    ])

    rows = []
    for dt in sorted(week_dts, key=lambda x: str(x.start_date or "")):
        planned_badge = _badge("Planned", "blue") if dt.planned else _badge("Unplanned", "red")
        rows.append([
            dt.asset_id or "—",
            _fmt_date(dt.start_date),
            _fmt_date(dt.end_date),
            f"<strong>{(dt.downtime_hours or 0):.1f}h</strong>",
            planned_badge,
            (dt.component_affected or "—")[:35],
            (dt.details or "—")[:50],
        ])
    tbl = _table(["Asset", "Start", "End", "Hours", "Planned", "Component", "Details"], rows)

    summary = f'<p style="font-size:13px;color:#64748b;margin:0 0 12px">Period: <strong style="color:#1e293b">{week.label()}</strong></p>'
    return _card("2. Downtime – Previous Week", summary + kpi + tbl, "⏱")


def _sec_downtime_month(d: dict) -> str:
    m_s, p_s = d["m_s"], d["p_s"]
    today      = d["today"]
    curr_hrs   = d["curr_month_hrs"]
    prev_hrs   = d["prev_like_hrs"]
    prev_like_end = d["prev_like_end"]
    curr_by    = d["curr_by_asset"]
    prev_by    = d["prev_like_by_asset"]

    # Like-for-like period labels
    curr_label = f"{m_s.strftime('%-d %b')} – {today.strftime('%-d %b %Y')}"
    prev_label = f"{p_s.strftime('%-d %b')} – {prev_like_end.strftime('%-d %b %Y')}"

    delta = curr_hrs - prev_hrs
    delta_str = f"+{delta:.1f}h" if delta >= 0 else f"{delta:.1f}h"
    delta_col = "red" if delta > 0 else "green"

    kpi = _kpi_row([
        (f"{curr_hrs:.1f}h", curr_label, "blue"),
        (f"{prev_hrs:.1f}h", prev_label, "slate"),
        (delta_str, "Change vs same period", delta_col),
    ])

    all_ids = sorted(set(curr_by) | set(prev_by))
    chart = ""
    if all_ids:
        mx = max(max(curr_by.values(), default=0), max(prev_by.values(), default=0), 1)
        rows_html = ""
        for asset in all_ids:
            c = curr_by.get(asset, 0)
            p = prev_by.get(asset, 0)
            rows_html += (
                f'<div style="margin-bottom:10px">'
                f'<div style="font-size:11px;font-weight:600;color:#1e293b;margin-bottom:4px">{asset}</div>'
                f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:3px">'
                f'<span style="font-size:10px;color:#64748b;width:70px">{p_s.strftime("%b %y")}</span>'
                f'{_css_bar(p, mx, "#94a3b8")}</div>'
                f'<div style="display:flex;align-items:center;gap:6px">'
                f'<span style="font-size:10px;color:#2563eb;width:70px">{m_s.strftime("%b %y")}</span>'
                f'{_css_bar(c, mx, "#2563eb")}</div>'
                f'</div>'
            )
        chart = (
            f'<div style="margin-top:16px">'
            f'<p style="font-size:12px;font-weight:600;color:#64748b;margin:0 0 4px">Downtime by Asset – Like-for-Like</p>'
            f'<p style="font-size:11px;color:#94a3b8;margin:0 0 12px">Both periods cover the same number of days (1st – {today.day}th of each month)</p>'
            f'{rows_html}</div>'
        )

    return _card("3. Downtime – Month Comparison (Like-for-Like)", kpi + chart, "📊")


def _sec_bales(d: dict) -> str:
    wb, wv = d["week_bales"]
    mb, mv = d["month_bales"]
    rows = [
        ["Previous Week", f"<strong>{wb:,}</strong>", f"<strong>{_fmt_money(wv)}</strong>"],
        ["Month to Date", f"<strong>{mb:,}</strong>", f"<strong>{_fmt_money(mv)}</strong>"],
    ]
    tbl = _table(["Period", "Bales Lost", "Est. Value (USD)"], rows)
    note = '<p style="font-size:11px;color:#94a3b8;margin:8px 0 0">Calculated from downtime hours × bale rate × commodity price.</p>'
    return _card("4. Bales Lost & Estimated Cost", tbl + note, "📦")


def _sec_work_orders(d: dict) -> str:
    week_wos, open_wos = d["week_wos"], d["open_wos"]
    week: WeekRange = d["week"]
    started   = [w for w in week_wos if week.contains(w.issue_date)]
    completed = [w for w in week_wos if week.contains(w.date_completed)]

    kpi = _kpi_row([
        (len(started),   "Started This Week",    "blue"),
        (len(completed), "Completed This Week",  "green"),
        (len(open_wos),  "Total Open",           "amber"),
    ])

    rows = []
    for w in sorted(week_wos, key=lambda x: str(x.issue_date or "")):
        pri = _val(w.priority) if w.priority else ""
        pri_col = {"high": "red", "High": "red", "medium": "amber", "Medium": "amber"}.get(pri, "slate")
        st = _val(w.status) if w.status else ""
        rows.append([
            f'<strong>WO-{w.work_order_id}</strong>',
            w.asset_id or "—",
            (_val(w.typ) or "—").replace("_", " ").title(),
            _badge(pri.title(), pri_col) if pri else "—",
            _badge(st.replace("_", " ").title(), "blue") if st else "—",
            _fmt_date(w.issue_date),
            _fmt_date(w.date_completed),
            (w.description or "—")[:55],
        ])
    tbl = _table(["WO #", "Asset", "Type", "Priority", "Status", "Issued", "Completed", "Description"], rows)

    # Open WOs by status
    status_counts: Counter = Counter(_val(w.status) for w in open_wos)
    open_html = ""
    if status_counts:
        mx = max(status_counts.values(), default=1)
        bars = "".join(
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
            f'<div style="width:130px;font-size:11px;color:#64748b;text-align:right;flex-shrink:0">{st.replace("_"," ").title()}</div>'
            f'{_css_bar(cnt, mx, "#2563eb")}</div>'
            for st, cnt in sorted(status_counts.items(), key=lambda x: -x[1])
        )
        open_html = (
            f'<div style="margin-top:20px">'
            f'<p style="font-size:12px;font-weight:600;color:#64748b;margin:0 0 10px">Open Work Orders by Status</p>'
            f'{bars}</div>'
        )

    return _card("5. Work Orders", kpi + tbl + open_html, "🔧")


def _sec_pm(d: dict) -> str:
    overdue, due_soon = d["overdue_pms"], d["due_soon_pms"]
    active_total = len([p for p in d["asset_pms"] if p.active])
    today = d["today"]
    pct = ((active_total - len(overdue)) / active_total * 100) if active_total else 0
    pct_col = "green" if pct >= 90 else "amber" if pct >= 70 else "red"

    kpi = _kpi_row([
        (active_total,     "Active PMs",        "blue"),
        (len(overdue),     "Overdue",           "red"),
        (len(due_soon),    "Due in 14 Days",    "amber"),
        (f"{pct:.0f}%",   "Compliance",        pct_col),
    ])

    rows = []
    for p in sorted(overdue, key=lambda x: _to_date(x.next_service) or date.max):
        ns = _to_date(p.next_service)
        days_od = (today - ns).days if ns else "—"
        rows.append([
            str(p.id), p.asset_id or "—", p.pm_plan_id or "—",
            _fmt_date(p.last_service), _fmt_date(p.next_service),
            f'<strong style="color:#dc2626">{days_od} days</strong>',
        ])
    tbl = _table(["PM ID", "Asset", "Plan", "Last Service", "Next Service", "Days Overdue"], rows)
    note = "" if rows else '<p style="font-size:12px;color:#16a34a;margin-top:8px">✓ No overdue PMs — fully compliant.</p>'
    return _card("6. PM Compliance", kpi + (tbl if rows else "") + note, "📅")


def _sec_finance(d: dict) -> str:
    month_bud, month_inv = d["month_bud"], d["month_inv"]
    prev_bud, prev_inv   = d["prev_bud"],  d["prev_inv"]
    m_s, p_s             = d["m_s"],       d["p_s"]

    total_bud  = sum(b.amount for b in month_bud)
    total_act  = sum(i.subtotal for i in month_inv)
    prev_bud_t = sum(b.amount for b in prev_bud)
    prev_act_t = sum(i.subtotal for i in prev_inv)
    variance   = total_bud - total_act

    kpi = _kpi_row([
        (_fmt_money(total_bud),  f"Budget ({m_s.strftime('%b %Y')})",  "blue"),
        (_fmt_money(total_act),  f"Actual ({m_s.strftime('%b %Y')})",  "amber"),
        (_fmt_money(variance),   "Variance",  "green" if variance >= 0 else "red"),
    ])

    rows = [
        [m_s.strftime("%B %Y"), _fmt_money(total_bud), _fmt_money(total_act),
         _fmt_money(variance),
         f"{total_act / total_bud * 100:.1f}%" if total_bud else "—"],
        [p_s.strftime("%B %Y"), _fmt_money(prev_bud_t), _fmt_money(prev_act_t),
         _fmt_money(prev_bud_t - prev_act_t),
         f"{prev_act_t / prev_bud_t * 100:.1f}%" if prev_bud_t else "—"],
    ]
    tbl = _table(["Period", "Budget", "Actual", "Variance", "Utilisation"], rows)

    # Budget by GL code bars
    bud_by_gl: dict[str, float] = defaultdict(float)
    for b in month_bud:
        if b.gl_code:
            bud_by_gl[b.gl_code] += b.amount
    chart = ""
    if bud_by_gl:
        mx = max(bud_by_gl.values())
        bars = "".join(
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
            f'<div style="width:120px;font-size:11px;color:#64748b;text-align:right;flex-shrink:0">{gl[:22]}</div>'
            f'{_css_bar(amt, mx, "#2563eb")}</div>'
            for gl, amt in sorted(bud_by_gl.items(), key=lambda x: -x[1])
        )
        chart = (
            f'<div style="margin-top:20px">'
            f'<p style="font-size:12px;font-weight:600;color:#64748b;margin:0 0 10px">Budget by GL Code – {m_s.strftime("%B %Y")}</p>'
            f'{bars}</div>'
        )

    return _card("7. Finance – Spend vs Budget", kpi + tbl + chart, "💰")


def _sec_issues(d: dict) -> str:
    open_iss, week_iss = d["open_iss"], d["week_iss"]

    kpi = _kpi_row([
        (len(open_iss),  "Open Issues",      "amber"),
        (len(week_iss),  "New This Week",    "blue"),
    ])

    rows = []
    sev_colors = {"critical": "red", "high": "amber", "medium": "blue", "low": "slate"}
    for iss in sorted(open_iss, key=lambda x: str(x.reported_at or ""), reverse=True):
        sev = _val(iss.severity) if iss.severity else ""
        st  = _val(iss.status)  if iss.status  else ""
        rows.append([
            f'<strong>#{iss.id}</strong>',
            iss.asset_id or "—",
            _badge(sev.title(), sev_colors.get(sev, "slate")) if sev else "—",
            _badge(st.replace("_", " ").title(), "blue") if st else "—",
            _fmt_date(_to_date(iss.reported_at)),
            (iss.description or "—")[:60],
        ])
    tbl = _table(["ID", "Asset", "Severity", "Status", "Reported", "Description"], rows)
    return _card("8. Issues", kpi + (tbl if rows else '<p style="color:#94a3b8;font-size:12px">No open issues.</p>'), "⚠️")


def _sec_reliability(d: dict) -> str:
    assets = d["assets"]
    m_s    = d["m_s"]
    curr_by_asset     = d["curr_by_asset"]   # properly attributed hours per asset, MTD
    scheduled_by_asset: dict[str, float] = d.get("scheduled_by_asset", {})

    # Count failure events per asset (events that started in the current month)
    month_dts = d["month_dts"]
    failures_by_asset: dict[str, int] = defaultdict(int)
    for dt in month_dts:
        if dt.asset_id:
            failures_by_asset[dt.asset_id] += 1

    rows = []
    avail_data = []
    for a in sorted(assets, key=lambda x: x.asset_id or ""):
        n       = failures_by_asset.get(a.asset_id, 0)
        dt_hrs  = curr_by_asset.get(a.asset_id, 0.0)
        sched   = scheduled_by_asset.get(a.asset_id, 0) or 0
        avail = max(0.0, (sched - dt_hrs) / sched * 100) if sched > 0 else 100.0
        mttr  = dt_hrs / n if n else None
        mtbf  = (sched - dt_hrs) / n if n else None
        avail_col = "#16a34a" if avail >= 90 else "#b45309" if avail >= 75 else "#dc2626"
        rows.append([
            f'<strong>{a.asset_id or "—"}</strong>',
            a.alias or "—",
            str(n),
            f"{dt_hrs:.1f}h",
            f"{mttr:.1f}h" if mttr is not None else "—",
            f"{mtbf:.1f}h" if mtbf is not None else "—",
            f'<strong style="color:{avail_col}">{avail:.1f}%</strong>',
        ])
        if a.asset_id:
            avail_data.append((a.asset_id, avail))

    tbl = _table(["Asset", "Alias", "Failures", "DT Hours", "MTTR", "MTBF", "Availability"], rows)

    chart = ""
    if avail_data:
        mx = 100
        sorted_avail = sorted(avail_data, key=lambda x: x[1])
        bars = "".join(
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">'
            f'<div style="width:110px;font-size:11px;color:#64748b;text-align:right;flex-shrink:0">{asset}</div>'
            f'<div style="flex:1;background:#f1f5f9;border-radius:4px;height:10px;overflow:hidden;position:relative">'
            f'<div style="width:{avail:.1f}%;background:{"#16a34a" if avail >= 90 else "#b45309" if avail >= 75 else "#dc2626"};height:100%;border-radius:4px"></div>'
            f'<div style="position:absolute;top:0;left:90%;width:1px;height:100%;background:#16a34a66"></div>'
            f'</div>'
            f'<span style="font-size:11px;color:#64748b;width:40px;text-align:right">{avail:.1f}%</span>'
            f'</div>'
            for asset, avail in sorted_avail
        )
        chart = (
            f'<div style="margin-top:20px">'
            f'<p style="font-size:12px;font-weight:600;color:#64748b;margin:0 0 10px">'
            f'Asset Availability – {m_s.strftime("%B %Y")} '
            f'<span style="font-size:10px;font-weight:400">(dotted line = 90% target)</span></p>'
            f'{bars}</div>'
        )

    note = '<p style="font-size:11px;color:#94a3b8;margin:8px 0 0">Scheduled hours calculated per asset from depot shift pattern (single or double shift).</p>'
    return _card(f"9. Reliability Summary – {m_s.strftime('%B %Y')}", tbl + chart + note, "📈")


# ── Main entry point ───────────────────────────────────────────────────────────

def generate_weekly_report_html(session: Session) -> str:
    d = _gather(session)
    week: WeekRange = d["week"]
    today = d["today"]

    sections = [
        _sec_assets(d),
        _sec_downtime_week(d),
        _sec_downtime_month(d),
        _sec_bales(d),
        _sec_work_orders(d),
        _sec_pm(d),
        _sec_finance(d),
        _sec_issues(d),
        _sec_reliability(d),
    ]

    body = "\n".join(sections)

    return print_page_shell(
        title=f"Weekly Maintenance Report – {week.label()}",
        subtitle="Weekly Report",
        header_title="Weekly Maintenance Report",
        header_meta=(
            f'<p>Generated {today.strftime("%A, %d %B %Y")}</p>'
            f'<div class="period">Period: {week.label()}</div>'
        ),
        body=body,
    )
