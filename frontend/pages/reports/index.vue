<script setup lang="ts">
import type { WorkOrder, Downtime, Issue, AssetPM, Asset, AssetModel, Budget, Invoice } from "~/types"
import type { CommodityRate } from "~/composables/useCommodityRates"

interface MonthlyMetrics {
  month: string
  scheduled_hours: number
  downtime_hours: number
  num_failures: number
  mttr: number | null
  mtbf: number | null
  availability: number
}

const { get } = useApi()
const { getAll: getCommodityRates } = useCommodityRates()

// ── Data fetches ───────────────────────────────────────────────
const { data: allAssets }          = useAsyncData("rpt-assets",            () => get<Asset[]>("/assets"))
const { data: assetModels }        = useAsyncData("rpt-asset-models",      () => get<AssetModel[]>("/asset-models"))
const { data: downtimes }          = useAsyncData("rpt-downtimes",         () => get<Downtime[]>("/downtimes"))
const { data: workOrders }         = useAsyncData("rpt-wos",               () => get<WorkOrder[]>("/work-orders"))
const { data: budgets }            = useAsyncData("rpt-budgets",           () => get<Budget[]>("/budgets"))
const { data: invoices }           = useAsyncData("rpt-invoices",          () => get<Invoice[]>("/invoices"))
const { data: monthlyMetricsData } = useAsyncData("rpt-monthly-metrics",   () => get<MonthlyMetrics[]>("/downtimes/monthly-metrics?months=12"))
const { data: commodityRates }     = await useAsyncData("rpt-commodity-rates", () => getCommodityRates())

// ── Timeline filter ────────────────────────────────────────────
const timelineOptions = [
  { label: "Last 7 days",   value: 7 },
  { label: "Last 30 days",  value: 30 },
  { label: "Last 90 days",  value: 90 },
  { label: "Last 6 months", value: 180 },
  { label: "Last year",     value: 365 },
  { label: "All time",      value: 0 },
]
const selectedDays = ref(30)

const dateRange = computed(() => {
  const to = new Date()
  if (!selectedDays.value) return { from: null, to }
  const from = new Date()
  from.setDate(to.getDate() - selectedDays.value)
  return { from, to }
})
const selectedLabel = computed(
  () => timelineOptions.find((o) => o.value === selectedDays.value)?.label ?? "Custom"
)

function inRange(dateStr: string | undefined | null, from: Date | null, to: Date) {
  if (!dateStr) return !from
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return false
  if (from && d < from) return false
  return d <= to
}

// ── Filtered data ──────────────────────────────────────────────
const filteredDowntimes = computed(() => {
  const { from, to } = dateRange.value
  return (downtimes.value ?? []).filter((d) => inRange(d.start_date ?? d.log_date, from, to))
})
const filteredWorkOrders = computed(() => {
  const { from, to } = dateRange.value
  return (workOrders.value ?? []).filter((w) => inRange(w.issue_date, from, to))
})
const filteredBudgets  = computed(() => {
  const { from, to } = dateRange.value
  return (budgets.value ?? []).filter((b) => inRange(b.month, from, to))
})
const filteredInvoices = computed(() => {
  const { from, to } = dateRange.value
  return (invoices.value ?? []).filter((i) => inRange(i.rec_date ?? i.job_date, from, to))
})

// ── Baler lookup: downtime.asset_id → asset.model_no → model specs ──
const assetModelNoMap = computed(() => {
  const m: Record<string, string> = {}
  for (const a of allAssets.value ?? [])
    if (a.model_no) m[a.asset_id] = a.model_no
  return m
})
const modelSpecMap = computed(() => {
  const m: Record<string, { bale_time: number; bale_weight: number }> = {}
  for (const am of assetModels.value ?? [])
    if (am.bale_time && am.bale_weight)
      m[am.model_no] = { bale_time: am.bale_time, bale_weight: am.bale_weight }
  return m
})

function rateAtDate(dateStr: string | null | undefined): number {
  if (!dateStr) return 0
  // rates are sorted DESC by effective_date from the API
  const applicable = (commodityRates.value ?? []).filter((r: CommodityRate) => r.effective_date <= dateStr)
  return applicable.length ? applicable[0].rate_per_lb : 0
}

function calcBales(events: Downtime[]) {
  let bales = 0, value = 0
  for (const d of events) {
    if (!d.asset_id || !d.downtime_hours) continue
    const modelNo = assetModelNoMap.value[d.asset_id]
    const specs = modelNo ? modelSpecMap.value[modelNo] : null
    if (!specs) continue
    const lost = d.downtime_hours * (60 / specs.bale_time)
    bales += lost
    const rate = rateAtDate(d.start_date ?? d.log_date)
    value += lost * specs.bale_weight * rate
  }
  return { bales: Math.round(bales), value }
}

const balesStats   = computed(() => calcBales(filteredDowntimes.value))

const currentMonthMetrics = computed(() => {
  const m = monthlyMetricsData.value ?? []
  return m[m.length - 1] ?? null
})
const prevMonthMetrics = computed(() => {
  const m = monthlyMetricsData.value ?? []
  return m[m.length - 2] ?? null
})
const totalDowntimeHrs = computed(() => currentMonthMetrics.value?.downtime_hours ?? 0)
const pmCost        = computed(() => filteredWorkOrders.value.filter((w) => w.typ === "preventative").reduce((s, w) => s + (w.actual_cost ?? 0), 0))
const correctiveCost = computed(() => filteredWorkOrders.value.filter((w) => w.typ === "corrective").reduce((s, w) => s + (w.actual_cost ?? 0), 0))
const totalBudget   = computed(() => filteredBudgets.value.reduce((s, b) => s + b.amount, 0))
const totalActual   = computed(() => filteredInvoices.value.reduce((s, i) => s + i.subtotal, 0))
const budgetVariance = computed(() => totalBudget.value - totalActual.value)

// ── Sparkline monthly data (last 6 months, independent of filter) ──
const last6 = (() => {
  const now = new Date()
  return Array.from({ length: 6 }, (_, i) => {
    const d = new Date(now.getFullYear(), now.getMonth() - (5 - i), 1)
    return { year: d.getFullYear(), month: d.getMonth() }
  })
})()

function monthlyDowntime() {
  const metricsMap = new Map((monthlyMetricsData.value ?? []).map((m) => [m.month, m.downtime_hours]))
  return last6.map(({ year, month }) => {
    const key = `${year}-${String(month + 1).padStart(2, "0")}`
    return +(metricsMap.get(key) ?? 0).toFixed(1)
  })
}
function monthlyBales() {
  return last6.map(({ year, month }) => {
    const evts = (downtimes.value ?? []).filter((d) => { const dt = new Date(d.start_date ?? d.log_date ?? ""); return dt.getFullYear() === year && dt.getMonth() === month })
    return calcBales(evts).bales
  })
}
function monthlyMaintCost() {
  return last6.map(({ year, month }) =>
    (workOrders.value ?? [])
      .filter((w) => { const dt = new Date(w.issue_date ?? ""); return dt.getFullYear() === year && dt.getMonth() === month && (w.typ === "preventative" || w.typ === "corrective") })
      .reduce((s, w) => s + (w.actual_cost ?? 0), 0)
  )
}
function monthlyBudgetUtil() {
  return last6.map(({ year, month }) => {
    const bud = (budgets.value ?? []).filter((b) => { const d = new Date(b.month); return d.getFullYear() === year && d.getMonth() === month }).reduce((s, b) => s + b.amount, 0)
    const act = (invoices.value ?? []).filter((i) => { const ds = i.rec_date ?? i.job_date; if (!ds) return false; const d = new Date(ds); return d.getFullYear() === year && d.getMonth() === month }).reduce((s, i) => s + i.subtotal, 0)
    return bud ? +Math.min((act / bud) * 100, 200).toFixed(1) : 0
  })
}

function trendVsLastMonth(data: number[]) {
  const curr = data[data.length - 1] ?? 0
  const prev = data[data.length - 2] ?? 0
  if (!prev) return { pct: "—", up: false }
  const pct = ((curr - prev) / prev) * 100
  return { pct: Math.abs(pct).toFixed(1), up: pct > 0 }
}

const kpiCards = computed(() => {
  const downData = monthlyDowntime()
  const baleData = monthlyBales()
  const maintData = monthlyMaintCost()
  const utilData = monthlyBudgetUtil()
  return [
    {
      id: "downtime",
      label: "Unplanned Downtime (this month)",
      value: totalDowntimeHrs.value.toFixed(1),
      suffix: "h",
      note: prevMonthMetrics.value ? `Last month: ${prevMonthMetrics.value.downtime_hours.toFixed(1)}h` : undefined,
      sparkData: downData,
      color: "#ef4444",
      trend: trendVsLastMonth(downData),
      higherIsBetter: false,
    },
    {
      id: "bales",
      label: "Bales Lost",
      value: balesStats.value.bales.toLocaleString(),
      suffix: "",
      note: fmtCurrency(balesStats.value.value) + " est.",
      sparkData: baleData,
      color: "#f97316",
      trend: trendVsLastMonth(baleData),
      higherIsBetter: false,
    },
    {
      id: "maint",
      label: "Maintenance Spend",
      value: fmtCurrency(pmCost.value + correctiveCost.value),
      suffix: "",
      note: `PM ${fmtCurrency(pmCost.value)} · COR ${fmtCurrency(correctiveCost.value)}`,
      sparkData: maintData,
      color: "#8b5cf6",
      trend: trendVsLastMonth(maintData),
      higherIsBetter: false,
    },
    {
      id: "budget",
      label: "Budget Utilisation",
      value: totalBudget.value ? ((totalActual.value / totalBudget.value) * 100).toFixed(1) + "%" : "—",
      suffix: "",
      note: (budgetVariance.value >= 0 ? "Under " : "Over ") + fmtCurrency(Math.abs(budgetVariance.value)),
      sparkData: utilData,
      color: budgetVariance.value >= 0 ? "#22c55e" : "#ef4444",
      trend: trendVsLastMonth(utilData),
      higherIsBetter: false,
    },
  ]
})

function sparkOpts(color: string) {
  return {
    chart: { type: "line", sparkline: { enabled: true }, animations: { enabled: false } },
    stroke: { width: 2, curve: "smooth" },
    colors: [color],
    tooltip: { enabled: false },
  }
}

// ── Formatters ─────────────────────────────────────────────────
function fmtCurrency(n: number) {
  if (Math.abs(n) >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`
  if (Math.abs(n) >= 1_000) return `$${(n / 1_000).toFixed(1)}k`
  return `$${n.toFixed(0)}`
}

// ── Report search & filter ─────────────────────────────────────
const searchQuery      = ref("")
const categoryFilter   = ref<string | null>(null)

// ── CSV helpers ─────────────────────────────────────────────────
function toCSV(headers: string[], rows: (string | number | boolean | null | undefined)[][]): string {
  const esc = (v: string | number | boolean | null | undefined) => `"${String(v ?? "").replace(/"/g, '""')}"`
  return [headers.map(esc).join(","), ...rows.map((r) => r.map(esc).join(","))].join("\n")
}
function triggerDownload(filename: string, csv: string) {
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a"); a.href = url; a.download = filename
  document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url)
}
function slugDate(d: Date) { return d.toISOString().slice(0, 10) }

// ── Download functions ─────────────────────────────────────────
async function downloadWorkOrders() {
  const data = await get<WorkOrder[]>("/work-orders")
  const { from, to } = dateRange.value
  const rows = (data ?? []).filter((w) => inRange(w.issue_date, from, to)).map((w) => [w.work_order_id, w.asset_id, w.priority, w.typ, w.status, w.issue_date, w.expected_date, w.date_completed, w.estimated_hours, w.actual_hours, w.estimated_cost, w.actual_cost, w.description, w.notes])
  triggerDownload(`work-orders-${slugDate(to)}.csv`, toCSV(["WO #", "Asset", "Priority", "Type", "Status", "Issue Date", "Expected Date", "Date Completed", "Est. Hours", "Actual Hours", "Est. Cost", "Actual Cost", "Description", "Notes"], rows))
}
async function downloadDowntime() {
  const [dt, causes] = await Promise.all([get<Downtime[]>("/downtimes"), get<{ cause_id: number; name: string }[]>("/downtimes/causes")])
  const causeMap: Record<number, string> = {}; for (const c of causes ?? []) if (c.cause_id) causeMap[c.cause_id] = c.name
  const { from, to } = dateRange.value
  const rows = (dt ?? []).filter((d) => inRange(d.start_date ?? d.log_date, from, to)).map((d) => [d.downtime_id, d.asset_id, d.cause_id ? (causeMap[d.cause_id] ?? d.cause_id) : "", d.start_date, d.start_time, d.end_date, d.end_time, d.downtime_hours, d.planned ? "Yes" : "No", d.component_affected, d.root_cause, d.corrective_action, d.repeat_failure ? "Yes" : "No", d.work_order])
  triggerDownload(`downtime-${slugDate(to)}.csv`, toCSV(["ID", "Asset", "Cause", "Start Date", "Start Time", "End Date", "End Time", "Downtime Hours", "Planned", "Component Affected", "Root Cause", "Corrective Action", "Repeat Failure", "Work Order"], rows))
}
async function downloadReliability() {
  const { from, to } = dateRange.value
  const months = await get<MonthlyMetrics[]>("/downtimes/monthly-metrics?months=12")
  const rows = (months ?? [])
    .filter((m) => {
      const [y, mo] = m.month.split("-").map(Number)
      const monthStart = new Date(y, mo - 1, 1)
      const monthEnd = new Date(y, mo, 0)
      if (from && monthEnd < from) return false
      if (monthStart > to) return false
      return true
    })
    .sort((a, b) => a.month.localeCompare(b.month))
    .map((m) => [
      m.month,
      m.num_failures,
      m.downtime_hours.toFixed(2),
      m.mttr != null ? m.mttr.toFixed(2) : "—",
      m.mtbf != null ? m.mtbf.toFixed(2) : "—",
      m.availability.toFixed(2) + "%",
    ])
  triggerDownload(`reliability-${slugDate(to)}.csv`, toCSV(["Month", "Failure Events", "Total Downtime (hrs)", "MTTR (hrs)", "MTBF (hrs)", "Availability"], rows))
}
async function downloadAssets() {
  const [assets, locs] = await Promise.all([get<any[]>("/assets"), get<{ location_id: number; name: string }[]>("/locations")])
  const locMap: Record<number, string> = {}; for (const l of locs ?? []) if (l.location_id) locMap[l.location_id] = l.name
  const { from } = dateRange.value
  const rows = (assets ?? []).filter((a) => !from || inRange(a.date_in_service, from, dateRange.value.to)).map((a) => [a.asset_id, a.manufacturer, a.model_no, a.yr, a.serial_no, a.category, a.status, a.sub_status, a.owned, a.alias, a.date_in_service, a.location_id ? (locMap[a.location_id] ?? a.location_id) : "", a.notes])
  triggerDownload(`assets-${slugDate(dateRange.value.to)}.csv`, toCSV(["Asset ID", "Manufacturer", "Model No", "Year", "Serial No", "Category", "Status", "Sub Status", "Ownership", "Alias", "Date In Service", "Location", "Notes"], rows))
}
async function downloadPMSchedule() {
  const pms = await get<AssetPM[]>("/maintenance/asset-pms"); const { from, to } = dateRange.value
  const rows = (pms ?? []).filter((p) => !from || inRange(p.next_service, from, to) || inRange(p.last_service, from, to)).map((p) => [p.id, p.asset_id, p.pm_plan_id, p.last_service, p.next_service, p.active ? "Active" : "Inactive"])
  triggerDownload(`pm-schedule-${slugDate(to)}.csv`, toCSV(["ID", "Asset", "PM Plan", "Last Service", "Next Service", "Status"], rows))
}
async function downloadIssues() {
  const [issues, users] = await Promise.all([get<Issue[]>("/issues"), get<{ id: number; firstname: string; lastname: string }[]>("/users")])
  const userMap: Record<number, string> = {}; for (const u of users ?? []) if (u.id) userMap[u.id] = `${u.firstname} ${u.lastname}`
  const { from, to } = dateRange.value
  const rows = (issues ?? []).filter((i) => inRange(i.reported_at, from, to)).map((i) => [i.id, i.asset_id, i.severity, i.status, i.reported_by ? (userMap[i.reported_by] ?? i.reported_by) : "", i.reported_at, i.work_order_id ?? "", i.description])
  triggerDownload(`issues-${slugDate(to)}.csv`, toCSV(["ID", "Asset", "Severity", "Status", "Reported By", "Reported At", "Work Order ID", "Description"], rows))
}
async function downloadBalesLost() {
  const dt = await get<Downtime[]>("/downtimes")
  const { from, to } = dateRange.value
  const filtered = (dt ?? []).filter((d) => inRange(d.start_date ?? d.log_date, from, to))
  const monthMap = new Map<string, Downtime[]>()
  for (const d of filtered) {
    const key = (d.start_date ?? d.log_date ?? "").slice(0, 7)
    if (!key) continue
    if (!monthMap.has(key)) monthMap.set(key, [])
    monthMap.get(key)!.push(d)
  }
  const rows = [...monthMap.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, events]) => {
      const { bales, value } = calcBales(events)
      return [month, bales, value.toFixed(2)]
    })
  triggerDownload(`bales-lost-${slugDate(to)}.csv`, toCSV(["Month", "Bales Lost", "Value (USD)"], rows))
}

async function downloadAvailabilityByCategory() {
  const { from, to } = dateRange.value
  const [catMetrics, assets, holidays, dt] = await Promise.all([
    get<{ month: string; category: string; downtime_hours: number; failures: number }[]>("/downtimes/monthly-metrics-by-category?months=24"),
    get<Asset[]>("/assets"),
    get<{ holiday_date: string }[]>("/holidays"),
    get<Downtime[]>("/downtimes"),
  ])

  const holidaySet = new Set((holidays ?? []).map(h => h.holiday_date.slice(0, 10)))

  // Build shift status per asset from downtime records (matches backend logic)
  const assetShiftMap: Record<string, boolean> = {}
  for (const d of dt ?? []) {
    if (d.asset_id != null) assetShiftMap[d.asset_id] = d.shift_asset ?? false
  }

  // Sum scheduled hours per working day per category (8h non-shift, 16h shift)
  const categoryHoursPerDay: Record<string, number> = {}
  for (const a of assets ?? []) {
    if (a.status !== "disposed") {
      const hrs = assetShiftMap[a.asset_id] ? 16 : 8
      categoryHoursPerDay[a.category] = (categoryHoursPerDay[a.category] ?? 0) + hrs
    }
  }

  function workingDays(y: number, m: number) {
    const days = new Date(y, m, 0).getDate()
    let n = 0
    for (let d = 1; d <= days; d++) {
      const date = new Date(y, m - 1, d)
      const dow = date.getDay()
      if (dow === 0 || dow === 6) continue
      if (!holidaySet.has(date.toISOString().slice(0, 10))) n++
    }
    return n
  }

  // Filter to selected date range and build lookup map
  const filtered = (catMetrics ?? []).filter(r => inRange(r.month + "-01", from, to))
  const dtMap: Record<string, number> = {}
  for (const r of filtered) dtMap[`${r.month}|${r.category}`] = r.downtime_hours

  const months = [...new Set(filtered.map(r => r.month))].sort()
  const categories = Object.keys(categoryHoursPerDay).sort()

  const headers = ["Month", ...categories.map(c => `${c} availability %`), ...categories.map(c => `${c} downtime hrs`)]
  const rows = months.map(month => {
    const [y, m] = month.split("-").map(Number)
    const wdays = workingDays(y, m)
    const row: (string | number)[] = [month]
    for (const cat of categories) {
      const dtHrs = dtMap[`${month}|${cat}`] ?? 0
      const scheduled = (categoryHoursPerDay[cat] ?? 0) * wdays
      row.push(scheduled > 0 ? (((scheduled - dtHrs) / scheduled) * 100).toFixed(1) + "%" : "100%")
    }
    for (const cat of categories) row.push((dtMap[`${month}|${cat}`] ?? 0).toFixed(1))
    return row
  })
  triggerDownload(`availability-by-category-${slugDate(to)}.csv`, toCSV(headers, rows))
}

async function downloadDowntimeByCategory() {
  const { from, to } = dateRange.value
  const catMetrics = await get<{ month: string; category: string; downtime_hours: number; failures: number }[]>("/downtimes/monthly-metrics-by-category?months=24")
  const rows = (catMetrics ?? [])
    .filter(r => inRange(r.month + "-01", from, to) && (r.downtime_hours > 0 || r.failures > 0))
    .sort((a, b) => a.month.localeCompare(b.month) || a.category.localeCompare(b.category))
    .map(r => [r.month, r.category, r.downtime_hours.toFixed(1), r.failures])
  triggerDownload(`downtime-by-category-${slugDate(to)}.csv`, toCSV(["Month", "Equipment Category", "Downtime Hours", "Failure Events"], rows))
}

async function downloadFailureDrivers() {
  const [dt, causes] = await Promise.all([get<Downtime[]>("/downtimes"), get<{ cause_id: number; name: string }[]>("/downtime-causes")])
  const causeMap: Record<number, string> = {}
  for (const c of causes ?? []) if (c.cause_id) causeMap[c.cause_id] = c.name
  const { from, to } = dateRange.value
  const map: Record<string, { hours: number; count: number }> = {}
  for (const d of dt ?? []) {
    if (d.planned || !d.downtime_hours) continue
    if (!inRange(d.start_date ?? d.log_date, from, to)) continue
    const cause = d.cause_id ? (causeMap[d.cause_id] ?? `Cause #${d.cause_id}`) : (d.root_cause?.trim() || "Unknown")
    if (!map[cause]) map[cause] = { hours: 0, count: 0 }
    map[cause].hours += d.downtime_hours; map[cause].count++
  }
  const totalHours = Object.values(map).reduce((s, v) => s + v.hours, 0)
  const rows = Object.entries(map)
    .sort(([, a], [, b]) => b.hours - a.hours)
    .map(([cause, { hours, count }]) => [cause, count, hours.toFixed(1), totalHours > 0 ? ((hours / totalHours) * 100).toFixed(1) + "%" : "0%"])
  triggerDownload(`failure-drivers-${slugDate(to)}.csv`, toCSV(["Cause", "Events", "Downtime Hours", "% of Total Downtime"], rows))
}

// ── Weekly HTML report ────────────────────────────────────────
const { token } = useAuth()
const config = useRuntimeConfig()
const generatingReport = ref(false)
const reportError = ref<string | null>(null)

async function openWeeklyReport() {
  generatingReport.value = true
  reportError.value = null
  try {
    const res = await fetch(`${config.public.apiBase}/reports/weekly-html`, {
      headers: { Authorization: `Bearer ${token.value}` },
    })
    if (!res.ok) throw new Error(`Server error ${res.status}`)
    const html = await res.text()
    const blob = new Blob([html], { type: "text/html" })
    const url = URL.createObjectURL(blob)
    const win = window.open(url, "_blank")
    if (win) setTimeout(() => URL.revokeObjectURL(url), 10_000)
  } catch (e: unknown) {
    reportError.value = (e as Error).message ?? "Failed to generate report"
  } finally {
    generatingReport.value = false
  }
}

const downloading = ref<string | null>(null)
const lastGenerated = reactive<Record<string, string>>({})
function makeDownloader(id: string, fn: () => Promise<void>) {
  return async () => { downloading.value = id; try { await fn(); lastGenerated[id] = new Date().toLocaleTimeString() } finally { downloading.value = null } }
}

interface ReportDef {
  id: string; name: string; description: string
  category: string; categoryColor: string; icon: string; dateNote: string
  download: () => Promise<void>
}

const reports: ReportDef[] = [
  { id: "work-orders",  name: "Work Orders Summary",            description: "All work orders with status, priority, cost and hours.",                      category: "Operations",  categoryColor: "info",    icon: "i-heroicons-clipboard-document-list",    dateNote: "By issue date",       download: makeDownloader("work-orders",  downloadWorkOrders) },
  { id: "downtime",     name: "Downtime Log",                   description: "Downtime events with root cause, action and hours lost.",                     category: "Operations",  categoryColor: "info",    icon: "i-heroicons-exclamation-triangle",        dateNote: "By start date",       download: makeDownloader("downtime",     downloadDowntime) },
  { id: "issues",       name: "Issues Log",                     description: "Reported issues with severity, status and resolution.",                       category: "Operations",  categoryColor: "info",    icon: "i-heroicons-flag",                        dateNote: "By reported date",    download: makeDownloader("issues",       downloadIssues) },
  { id: "bales-lost",   name: "Bales Lost",                     description: "Monthly bales lost and estimated value using historical commodity rates.",    category: "Operations",  categoryColor: "info",    icon: "i-heroicons-cube",                        dateNote: "Monthly aggregation", download: makeDownloader("bales-lost",   downloadBalesLost) },
  { id: "reliability",  name: "Reliability Summary (MTTR/MTBF)", description: "Monthly MTTR and MTBF breakdown over the selected period.",                  category: "Reliability", categoryColor: "warning", icon: "i-heroicons-chart-bar",                   dateNote: "Monthly aggregation", download: makeDownloader("reliability",  downloadReliability) },
  { id: "assets",       name: "Asset Inventory",                description: "Full asset register with status, ownership and location.",                    category: "Assets",      categoryColor: "success", icon: "i-heroicons-wrench-screwdriver",           dateNote: "Current state",       download: makeDownloader("assets",       downloadAssets) },
  { id: "pm-schedule",  name: "PM Schedule",                    description: "Preventative maintenance schedules with last and next service.",              category: "Maintenance", categoryColor: "neutral", icon: "i-heroicons-calendar-days",               dateNote: "By service dates",    download: makeDownloader("pm-schedule",  downloadPMSchedule) },
  { id: "avail-by-cat", name: "Availability by Equipment Category", description: "Monthly availability % and downtime hours per equipment category (baler, forklift, etc.).", category: "Reliability", categoryColor: "warning", icon: "i-heroicons-table-cells", dateNote: "Monthly aggregation", download: makeDownloader("avail-by-cat", downloadAvailabilityByCategory) },
  { id: "dt-by-cat",    name: "Downtime by Equipment Category", description: "Unplanned downtime hours and failure events aggregated by equipment category per month.", category: "Reliability", categoryColor: "warning", icon: "i-heroicons-squares-2x2",                 dateNote: "Monthly aggregation", download: makeDownloader("dt-by-cat",    downloadDowntimeByCategory) },
  { id: "failure-drv",  name: "Failure Drivers",                description: "Downtime events and hours grouped by root cause, sorted by highest impact.",  category: "Reliability", categoryColor: "warning", icon: "i-heroicons-exclamation-circle",           dateNote: "By start date",       download: makeDownloader("failure-drv",  downloadFailureDrivers) },
]

const filteredReports = computed(() =>
  reports.filter((r) => {
    const matchQ = !searchQuery.value || r.name.toLowerCase().includes(searchQuery.value.toLowerCase()) || r.category.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchCat = !categoryFilter.value || r.category === categoryFilter.value
    return matchQ && matchCat
  })
)

const reportCategories = computed(() => {
  const map = new Map<string, { icon: string; color: string; count: number; categoryColor: string }>()
  for (const r of reports) {
    if (!map.has(r.category)) map.set(r.category, { icon: r.icon, color: r.categoryColor, count: 0, categoryColor: r.categoryColor })
    map.get(r.category)!.count++
  }
  return [...map.entries()].map(([name, d]) => ({ name, ...d }))
})

const exportingAll = ref(false)
async function exportAll() {
  exportingAll.value = true
  try { for (const r of filteredReports.value) await r.download() }
  finally { exportingAll.value = false }
}
</script>

<template>
  <div class="space-y-5">

    <!-- ── Weekly Management Report ───────────────────────────── -->
    <div class="flex items-center justify-between rounded-xl border border-blue-100 bg-blue-50 px-5 py-4">
      <div class="flex items-center gap-4">
        <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-600">
          <UIcon name="i-heroicons-document-chart-bar" class="h-5 w-5 text-white" />
        </div>
        <div>
          <p class="text-sm font-semibold text-slate-800">Weekly Management Report</p>
          <p class="text-xs text-slate-500">Covers the previous Mon – Sun. Includes downtime, work orders, PM compliance, finance and reliability. Opens in a new tab — print or save as PDF from there.</p>
        </div>
      </div>
      <div class="flex flex-col items-end gap-1">
        <UButton leading-icon="i-heroicons-arrow-top-right-on-square" :loading="generatingReport" @click="openWeeklyReport">
          Open Report
        </UButton>
        <p v-if="reportError" class="text-xs text-red-500">{{ reportError }}</p>
      </div>
    </div>

    <!-- ── Header ──────────────────────────────────────────────── -->
    <div class="flex flex-wrap items-center gap-3">
        <div class="relative">
          <UIcon name="i-heroicons-magnifying-glass" class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search reports..."
            class="h-9 rounded-lg border border-slate-200 bg-white pl-9 pr-4 text-sm text-slate-700 placeholder-slate-400 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
          />
        </div>
        <UButton :loading="exportingAll" leading-icon="i-heroicons-arrow-down-tray" @click="exportAll">
          Export All
        </UButton>
    </div>

    <!-- ── KPI Sparkline Cards ─────────────────────────────────── -->
    <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <div
        v-for="card in kpiCards"
        :key="card.id"
        class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="min-w-0 flex-1">
            <p class="text-xs font-medium text-slate-500">{{ card.label }}</p>
            <p class="mt-1.5 text-2xl font-bold text-slate-900">{{ card.value }}<span v-if="card.suffix" class="ml-0.5 text-sm font-medium text-slate-400">{{ card.suffix }}</span></p>
          </div>
          <div class="w-24 shrink-0">
            <ClientOnly>
              <apexchart type="line" width="96" height="55" :options="sparkOpts(card.color)" :series="[{ data: card.sparkData }]" />
            </ClientOnly>
          </div>
        </div>
        <p v-if="card.note" class="mt-1 truncate text-xs text-slate-400">{{ card.note }}</p>
        <div class="mt-2 flex items-center gap-1 text-xs">
          <UIcon
            :name="card.trend.up ? 'i-heroicons-arrow-trending-up' : 'i-heroicons-arrow-trending-down'"
            class="h-3.5 w-3.5"
            :class="(card.trend.up && !card.higherIsBetter) || (!card.trend.up && card.higherIsBetter) ? 'text-red-500' : 'text-green-500'"
          />
          <span :class="(card.trend.up && !card.higherIsBetter) || (!card.trend.up && card.higherIsBetter) ? 'text-red-500' : 'text-green-500'">
            {{ card.trend.pct }}{{ card.trend.pct !== "—" ? "%" : "" }}
          </span>
          <span class="text-slate-400">vs last month</span>
        </div>
      </div>
    </div>

    <!-- ── Main two-column layout ──────────────────────────────── -->
    <div class="grid grid-cols-1 gap-5 lg:grid-cols-3">

      <!-- Left: reports list + spend chart -->
      <div class="space-y-5 lg:col-span-2">

        <!-- Filter bar -->
        <div class="flex flex-wrap items-center gap-3">
          <div class="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm">
            <UIcon name="i-heroicons-calendar" class="h-4 w-4 text-slate-400" />
            <select
              v-model="selectedDays"
              class="bg-transparent text-sm text-slate-700 focus:outline-none"
            >
              <option v-for="opt in timelineOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
            </select>
          </div>
          <div class="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm">
            <UIcon name="i-heroicons-funnel" class="h-4 w-4 text-slate-400" />
            <select
              v-model="categoryFilter"
              class="bg-transparent text-sm text-slate-700 focus:outline-none"
            >
              <option :value="null">All Types</option>
              <option v-for="cat in reportCategories" :key="cat.name" :value="cat.name">{{ cat.name }}</option>
            </select>
          </div>
          <div v-if="categoryFilter || searchQuery" class="ml-auto">
            <button class="text-xs text-blue-600 hover:underline" @click="categoryFilter = null; searchQuery = ''">Clear filters</button>
          </div>
        </div>

        <!-- Available Reports -->
        <div class="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
          <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
            <h2 class="text-sm font-semibold text-slate-900">Available Reports</h2>
            <span class="text-xs text-slate-400">{{ filteredReports.length }} report{{ filteredReports.length === 1 ? "" : "s" }}</span>
          </div>

          <div v-if="filteredReports.length" class="divide-y divide-slate-50">
            <div
              v-for="report in filteredReports"
              :key="report.id"
              class="flex items-center gap-4 px-5 py-4 transition-colors hover:bg-slate-50"
            >
              <!-- Icon -->
              <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100">
                <UIcon :name="report.icon" class="h-5 w-5 text-slate-500" />
              </div>

              <!-- Meta -->
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium text-slate-900">{{ report.name }}</p>
                <p class="mt-0.5 flex items-center gap-1.5 text-xs text-slate-400">
                  <UBadge :color="report.categoryColor" variant="soft" size="xs">{{ report.category }}</UBadge>
                  <span>·</span>
                  <span>{{ report.dateNote }}</span>
                  <span v-if="lastGenerated[report.id]">· {{ lastGenerated[report.id] }}</span>
                </p>
              </div>

              <!-- Ready + Download -->
              <div class="flex shrink-0 items-center gap-3">
                <UBadge color="success" variant="soft" size="xs">Ready</UBadge>
                <button
                  class="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 shadow-sm transition hover:border-blue-300 hover:text-blue-600 disabled:cursor-not-allowed disabled:opacity-40"
                  :disabled="!!downloading && downloading !== report.id"
                  :title="`Download ${report.name}`"
                  @click="report.download"
                >
                  <UIcon v-if="downloading === report.id" name="i-heroicons-arrow-path" class="h-4 w-4 animate-spin" />
                  <UIcon v-else name="i-heroicons-arrow-down-tray" class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          <div v-else class="flex flex-col items-center gap-2 py-12 text-slate-400">
            <UIcon name="i-heroicons-document-magnifying-glass" class="h-8 w-8" />
            <p class="text-sm">No reports match your filters.</p>
          </div>
        </div>

      </div>

      <!-- Right sidebar -->
      <div class="space-y-5">

        <!-- Report Categories -->
        <div class="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
          <div class="border-b border-slate-100 px-5 py-4">
            <h2 class="text-sm font-semibold text-slate-900">Report Categories</h2>
          </div>
          <div class="divide-y divide-slate-50">
            <button
              v-for="cat in reportCategories"
              :key="cat.name"
              class="flex w-full items-center gap-3 px-5 py-3.5 text-left transition-colors hover:bg-slate-50"
              :class="categoryFilter === cat.name ? 'bg-blue-50' : ''"
              @click="categoryFilter = categoryFilter === cat.name ? null : cat.name"
            >
              <div :class="`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-${cat.color === 'info' ? 'blue' : cat.color === 'warning' ? 'amber' : cat.color === 'success' ? 'green' : 'slate'}-50`">
                <UIcon :name="cat.icon" :class="`h-4 w-4 text-${cat.color === 'info' ? 'blue' : cat.color === 'warning' ? 'amber' : cat.color === 'success' ? 'green' : 'slate'}-500`" />
              </div>
              <div class="flex-1">
                <p class="text-sm font-medium text-slate-800">{{ cat.name }}</p>
                <p class="text-xs text-slate-400">{{ cat.count }} report{{ cat.count === 1 ? "" : "s" }}</p>
              </div>
              <UIcon name="i-heroicons-chevron-right" class="h-4 w-4 text-slate-300" :class="categoryFilter === cat.name ? 'text-blue-400' : ''" />
            </button>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
          <div class="border-b border-slate-100 px-5 py-4">
            <h2 class="text-sm font-semibold text-slate-900">Quick Stats</h2>
            <p class="text-xs text-slate-400">{{ selectedLabel }}</p>
          </div>
          <div class="divide-y divide-slate-50 px-5">
            <!-- Downtime -->
            <div class="flex items-center justify-between py-3">
              <div>
                <span class="flex items-center gap-2 text-sm text-slate-600">
                  <UIcon name="i-heroicons-exclamation-triangle" class="h-4 w-4 text-red-400" />
                  Unplanned Downtime
                </span>
                <p class="mt-0.5 text-xs text-slate-400">This month</p>
              </div>
              <span class="font-semibold text-slate-900">{{ totalDowntimeHrs.toFixed(1) }}h</span>
            </div>
            <!-- Bales -->
            <div class="flex items-center justify-between py-3">
              <div>
                <span class="flex items-center gap-2 text-sm text-slate-600">
                  <UIcon name="i-heroicons-cube" class="h-4 w-4 text-amber-400" />
                  Bales Lost
                </span>
                <p class="mt-0.5 text-xs text-slate-400">At historical $/lb rates</p>
              </div>
              <div class="text-right">
                <p class="font-semibold text-slate-900">{{ balesStats.bales.toLocaleString() }}</p>
                <p class="text-xs text-slate-400">{{ fmtCurrency(balesStats.value) }}</p>
              </div>
            </div>
            <!-- PM -->
            <div class="flex items-center justify-between py-3">
              <span class="flex items-center gap-2 text-sm text-slate-600">
                <UIcon name="i-heroicons-calendar-days" class="h-4 w-4 text-purple-400" />
                PM Cost
              </span>
              <span class="font-semibold text-slate-900">{{ fmtCurrency(pmCost) }}</span>
            </div>
            <!-- Corrective -->
            <div class="flex items-center justify-between py-3">
              <span class="flex items-center gap-2 text-sm text-slate-600">
                <UIcon name="i-heroicons-wrench" class="h-4 w-4 text-blue-400" />
                Corrective Cost
              </span>
              <span class="font-semibold text-slate-900">{{ fmtCurrency(correctiveCost) }}</span>
            </div>
            <!-- Budget -->
            <div class="flex items-center justify-between py-3">
              <span class="flex items-center gap-2 text-sm text-slate-600">
                <UIcon name="i-heroicons-banknotes" class="h-4 w-4 text-green-400" />
                Budget
              </span>
              <div class="text-right">
                <UBadge :color="budgetVariance >= 0 ? 'success' : 'error'" variant="soft" size="xs">
                  {{ budgetVariance >= 0 ? "Under" : "Over" }} {{ fmtCurrency(Math.abs(budgetVariance)) }}
                </UBadge>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
