"""Small HTML-building helpers shared by the browser-readable report
generators (weekly report, work order print view, ...). Kept dependency-free
(plain string building, inline styles) so generated pages render standalone
and print cleanly without an external stylesheet.
"""

from utils.weekly_report import _to_date


def val(enum_or_str) -> str:
    """Return the plain string value of a str-enum or plain string."""
    if enum_or_str is None:
        return ""
    return enum_or_str.value if hasattr(enum_or_str, "value") else str(enum_or_str)


def fmt_date(v) -> str:
    d = _to_date(v)
    return d.strftime("%d-%b-%y") if d else "—"


def fmt_money(v) -> str:
    if v is None:
        return "—"
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:.2f}M"
    if abs(v) >= 1_000:
        return f"${v / 1_000:.1f}k"
    return f"${v:,.0f}"


def badge(text: str, color: str) -> str:
    palettes = {
        "green": ("background:#dcfce7;color:#16a34a", "16a34a"),
        "amber": ("background:#fef3c7;color:#b45309", "b45309"),
        "red": ("background:#fee2e2;color:#dc2626", "dc2626"),
        "blue": ("background:#dbeafe;color:#2563eb", "2563eb"),
        "slate": ("background:#f1f5f9;color:#64748b", "64748b"),
    }
    style, _ = palettes.get(color, palettes["slate"])
    return f'<span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;{style}">{text}</span>'


def table(headers: list, rows: list, col_styles: list | None = None) -> str:
    col_styles = col_styles or [""] * len(headers)
    th_cells = "".join(f'<th style="text-align:left;padding:7px 10px;font-size:11px;font-weight:600;white-space:nowrap;{s}">{h}</th>'
                        for h, s in zip(headers, col_styles))
    body = ""
    for i, row in enumerate(rows):
        bg = "#ffffff" if i % 2 == 0 else "#f8fafc"
        td_cells = "".join(
            f'<td style="padding:6px 10px;font-size:12px;border-bottom:1px solid #f1f5f9;vertical-align:middle;{col_styles[j] if j < len(col_styles) else ""}">{cell}</td>'
            for j, cell in enumerate(row)
        )
        body += f'<tr style="background:{bg}">{td_cells}</tr>'
    if not rows:
        body = f'<tr><td colspan="{len(headers)}" style="padding:16px 10px;text-align:center;color:#94a3b8;font-size:12px">No data available</td></tr>'
    return (
        f'<div style="overflow-x:auto;border-radius:8px;border:1px solid #e2e8f0;margin-top:10px">'
        f'<table style="width:100%;border-collapse:collapse">'
        f'<thead><tr style="background:#2563eb">{th_cells}</tr></thead>'
        f'<tbody>{body}</tbody>'
        f'</table></div>'
    )


def card(title: str, content: str, icon: str = "") -> str:
    return (
        f'<div style="background:#ffffff;border-radius:12px;border:1px solid #e2e8f0;'
        f'padding:24px;margin-bottom:24px;box-shadow:0 1px 3px rgba(0,0,0,.06)">'
        f'<h2 style="font-size:15px;font-weight:700;color:#1e293b;margin:0 0 16px;'
        f'display:flex;align-items:center;gap:8px">'
        f'<span style="color:#2563eb">{icon}</span>{title}</h2>'
        f'{content}</div>'
    )


def print_page_shell(*, title: str, subtitle: str, header_title: str, header_meta: str, body: str) -> str:
    """Wraps report `body` HTML in the standard toolbar + gradient header +
    print stylesheet used by all browser-readable report pages."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
             background: #f8fafc; color: #1e293b; line-height: 1.5; }}
    .toolbar {{ position: sticky; top: 0; z-index: 100; background: #1e293b;
                padding: 12px 32px; display: flex; align-items: center;
                justify-content: space-between; box-shadow: 0 2px 8px rgba(0,0,0,.2); }}
    .toolbar-brand {{ display: flex; align-items: center; gap: 12px; }}
    .toolbar-brand .logo {{ width: 32px; height: 32px; background: #2563eb;
                            border-radius: 8px; display: flex; align-items: center;
                            justify-content: center; font-size: 16px; }}
    .toolbar-brand h1 {{ font-size: 14px; font-weight: 700; color: #ffffff; }}
    .toolbar-brand p  {{ font-size: 11px; color: #94a3b8; }}
    .toolbar-actions {{ display: flex; gap: 8px; }}
    .btn {{ padding: 7px 16px; border-radius: 7px; font-size: 12px; font-weight: 600;
             cursor: pointer; border: none; display: flex; align-items: center; gap: 6px; }}
    .btn-primary {{ background: #2563eb; color: #fff; }}
    .btn-primary:hover {{ background: #1d4ed8; }}
    .btn-ghost {{ background: rgba(255,255,255,.1); color: #e2e8f0; }}
    .btn-ghost:hover {{ background: rgba(255,255,255,.2); }}
    .report-header {{ background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
                      padding: 48px 32px 40px; color: #fff; }}
    .report-header h1 {{ font-size: 28px; font-weight: 800; margin-bottom: 6px; }}
    .report-header p  {{ font-size: 14px; color: rgba(255,255,255,.75); }}
    .report-header .period {{ display: inline-block; background: rgba(255,255,255,.15);
                              padding: 4px 12px; border-radius: 20px; font-size: 12px;
                              font-weight: 600; margin-top: 12px; }}
    .content {{ max-width: 1100px; margin: 0 auto; padding: 32px 24px 64px; }}
    @media print {{
      .toolbar {{ display: none; }}
      body {{ background: #fff; }}
      .report-header {{ background: #2563eb !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
      .content {{ padding: 16px 0; }}
      div[style*="box-shadow"] {{ box-shadow: none !important; border: 1px solid #e2e8f0 !important; }}
    }}
  </style>
</head>
<body>

  <!-- Toolbar -->
  <div class="toolbar">
    <div class="toolbar-brand">
      <div class="logo">🔧</div>
      <div>
        <h1>Maintenance Manager</h1>
        <p>{subtitle}</p>
      </div>
    </div>
    <div class="toolbar-actions">
      <button class="btn btn-ghost" onclick="window.close()">✕ Close</button>
      <button class="btn btn-primary" onclick="window.print()">🖨 Print / Save PDF</button>
    </div>
  </div>

  <!-- Report header -->
  <div class="report-header">
    <h1>{header_title}</h1>
    {header_meta}
  </div>

  <!-- Sections -->
  <div class="content">
    {body}
  </div>

</body>
</html>"""
