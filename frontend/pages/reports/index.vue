<script setup lang="ts">
import type { WorkOrder, Downtime, Issue, AssetPM, Asset, AssetModel, Budget, Invoice, Location } from "~/types"
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
const { data: holidays }           = useAsyncData("rpt-holidays",          () => get<{ holiday_date: string }[]>("/holidays"))
const { data: locations }          = useAsyncData("rpt-locations",         () => get<Location[]>("/depots"))

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
  const [catMetrics, assets, hols, dt] = await Promise.all([
    get<{ month: string; category: string; downtime_hours: number; failures: number }[]>("/downtimes/monthly-metrics-by-category?months=24"),
    get<Asset[]>("/assets"),
    get<{ holiday_date: string }[]>("/holidays"),
    get<Downtime[]>("/downtimes"),
  ])

  const holSet = new Set((hols ?? []).map(h => h.holiday_date.slice(0, 10)))

  const assetShiftMap: Record<string, boolean> = {}
  for (const d of dt ?? []) {
    if (d.asset_id != null) assetShiftMap[d.asset_id] = d.shift_asset ?? false
  }

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
      if (!holSet.has(date.toISOString().slice(0, 10))) n++
    }
    return n
  }

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

// ── Asset Analysis ─────────────────────────────────────────────
const activeReportTab = ref<'reports' | 'asset' | 'location'>('reports')
const selectedAssetId = ref<string | null>(null)

const locationMap = computed(() => {
  const m: Record<number, string> = {}
  for (const l of locations.value ?? []) if (l.location_id) m[l.location_id] = l.name
  return m
})

const holidaySet = computed(() =>
  new Set((holidays.value ?? []).map(h => h.holiday_date.slice(0, 10)))
)

function workingDaysInMonth(year: number, month: number): number {
  // month is 0-based
  const days = new Date(year, month + 1, 0).getDate()
  let n = 0
  for (let d = 1; d <= days; d++) {
    const date = new Date(year, month, d)
    if (date.getDay() === 0 || date.getDay() === 6) continue
    const key = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    if (!holidaySet.value.has(key)) n++
  }
  return n
}

const analysisMonths = computed(() => {
  const now = new Date()
  return Array.from({ length: 12 }, (_, i) => {
    const d = new Date(now.getFullYear(), now.getMonth() - (11 - i), 1)
    return {
      year: d.getFullYear(),
      month: d.getMonth(),
      key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
      label: d.toLocaleString('default', { month: 'short', year: '2-digit' }),
    }
  })
})

const selectedAssetObj = computed(() =>
  (allAssets.value ?? []).find(a => a.asset_id === selectedAssetId.value) ?? null
)

const selectedAssetModel = computed(() => {
  const modelNo = selectedAssetObj.value?.model_no
  if (!modelNo) return null
  return (assetModels.value ?? []).find(m => m.model_no === modelNo) ?? null
})

const isBaler = computed(() => selectedAssetObj.value?.category === 'baler')

const assetDowntimes = computed(() =>
  (downtimes.value ?? []).filter(d => d.asset_id === selectedAssetId.value)
)

const assetWorkOrders = computed(() =>
  (workOrders.value ?? []).filter(w => w.asset_id === selectedAssetId.value)
)

const assetInvoices = computed(() =>
  (invoices.value ?? []).filter(i => i.asset_id === selectedAssetId.value)
)

const assetShiftHours = computed(() => {
  const rec = assetDowntimes.value.find(d => d.shift_asset !== undefined && d.shift_asset !== null)
  return rec?.shift_asset ? 16 : 8
})

const assetMonthlyDowntime = computed(() =>
  analysisMonths.value.map(({ year, month }) =>
    +assetDowntimes.value
      .filter(d => {
        const dt = new Date(d.start_date ?? d.log_date ?? '')
        return dt.getFullYear() === year && dt.getMonth() === month
      })
      .reduce((s, d) => s + (d.downtime_hours ?? 0), 0)
      .toFixed(1)
  )
)

const assetMonthlyAvailability = computed(() =>
  analysisMonths.value.map(({ year, month }, idx) => {
    const scheduled = workingDaysInMonth(year, month) * assetShiftHours.value
    if (!scheduled) return 100
    const dt = assetMonthlyDowntime.value[idx]
    return +Math.max(0, ((scheduled - dt) / scheduled) * 100).toFixed(1)
  })
)

const lifetimeDowntimeHrs = computed(() =>
  assetDowntimes.value.reduce((s, d) => s + (d.downtime_hours ?? 0), 0)
)

const lifetimeCostWO = computed(() =>
  assetWorkOrders.value.reduce((s, w) => s + (w.actual_cost ?? 0), 0)
)

const lifetimeCostInv = computed(() =>
  assetInvoices.value.reduce((s, i) => s + (i.subtotal ?? 0), 0)
)

const openWOStatuses = ['requested', 'scheduled', 'awaiting_parts', 'awaiting_po', 'in_progress', 'on_hold']

const woByType = computed(() =>
  ['corrective', 'preventative', 'predictive', 'inspection', 'project']
    .map(t => ({
      type: t,
      count: assetWorkOrders.value.filter(w => w.typ === t).length,
      cost: assetWorkOrders.value.filter(w => w.typ === t).reduce((s, w) => s + (w.actual_cost ?? 0), 0),
      hours: assetWorkOrders.value.filter(w => w.typ === t).reduce((s, w) => s + (w.actual_hours ?? 0), 0),
    }))
    .filter(t => t.count > 0)
)

const woOpen = computed(() =>
  assetWorkOrders.value.filter(w => openWOStatuses.includes(w.status)).length
)
const woCompleted = computed(() =>
  assetWorkOrders.value.filter(w => w.status === 'completed' || w.status === 'closed').length
)

const assetBalesStats = computed(() =>
  isBaler.value ? calcBales(assetDowntimes.value) : null
)

const avg12mAvailability = computed(() => {
  const vals = assetMonthlyAvailability.value
  if (!vals.length) return 100
  return +(vals.reduce((s, v) => s + v, 0) / vals.length).toFixed(1)
})

const assetSelectOptions = computed(() =>
  (allAssets.value ?? [])
    .sort((a, b) => a.asset_id.localeCompare(b.asset_id))
    .map(a => ({
      label: `${a.asset_id}${a.alias ? ' — ' + a.alias : ''} (${a.manufacturer})`,
      value: a.asset_id,
    }))
)

function assetStatusColor(status: string) {
  if (status === 'operational') return 'success'
  if (status === 'maintenance') return 'warning'
  if (status === 'disposed') return 'neutral'
  return 'error'
}

function woTypeColor(type: string) {
  if (type === 'corrective') return 'error'
  if (type === 'preventative') return 'success'
  if (type === 'predictive') return 'warning'
  if (type === 'inspection') return 'info'
  return 'neutral'
}

const dtBarOpts = computed(() => ({
  chart: { type: 'bar', toolbar: { show: false }, animations: { enabled: false } },
  plotOptions: { bar: { borderRadius: 3, columnWidth: '55%' } },
  dataLabels: { enabled: false },
  colors: ['#ef4444'],
  xaxis: {
    categories: analysisMonths.value.map(m => m.label),
    labels: { style: { fontSize: '11px' } },
  },
  yaxis: { title: { text: 'Hours' }, labels: { formatter: (v: number) => v.toFixed(1) } },
  tooltip: { y: { formatter: (v: number) => v.toFixed(1) + ' hrs' } },
  grid: { borderColor: '#f1f5f9' },
}))

const availLineOpts = computed(() => ({
  chart: { type: 'line', toolbar: { show: false }, animations: { enabled: false } },
  stroke: { width: 2, curve: 'smooth' },
  colors: ['#22c55e'],
  markers: { size: 4 },
  dataLabels: { enabled: false },
  xaxis: {
    categories: analysisMonths.value.map(m => m.label),
    labels: { style: { fontSize: '11px' } },
  },
  yaxis: {
    min: 0,
    max: 100,
    title: { text: 'Availability %' },
    labels: { formatter: (v: number) => v + '%' },
  },
  annotations: {
    yaxis: [{
      y: 90,
      borderColor: '#f97316',
      label: { text: '90% target', style: { color: '#fff', background: '#f97316' } },
    }],
  },
  tooltip: { y: { formatter: (v: number) => v.toFixed(1) + '%' } },
  grid: { borderColor: '#f1f5f9' },
}))

// ── Location Analysis ──────────────────────────────────────────
const selectedLocationId = ref<number | null>(null)

const selectedLocationObj = computed(() =>
  (locations.value ?? []).find(l => l.location_id === selectedLocationId.value) ?? null
)

const locationSelectOptions = computed(() =>
  (locations.value ?? [])
    .sort((a, b) => a.name.localeCompare(b.name))
    .map(l => ({
      label: `${l.name} (${l.typ === 'depot' ? 'Depot' : 'Redemption Centre'})`,
      value: l.location_id,
    }))
)

const locationAssets = computed(() =>
  (allAssets.value ?? []).filter(a => a.location_id === selectedLocationId.value)
)

const locationAssetIds = computed(() => new Set(locationAssets.value.map(a => a.asset_id)))

const locationDowntimes = computed(() =>
  (downtimes.value ?? []).filter(d => d.asset_id != null && locationAssetIds.value.has(d.asset_id))
)

const locationWorkOrders = computed(() =>
  (workOrders.value ?? []).filter(w => w.asset_id != null && locationAssetIds.value.has(w.asset_id))
)

const locationInvoices = computed(() =>
  (invoices.value ?? []).filter(i => i.asset_id != null && locationAssetIds.value.has(i.asset_id!))
)

const locationAssetShiftMap = computed(() => {
  const m: Record<string, number> = {}
  for (const a of locationAssets.value) {
    const rec = locationDowntimes.value.find(d => d.asset_id === a.asset_id && d.shift_asset !== undefined && d.shift_asset !== null)
    m[a.asset_id] = rec?.shift_asset ? 16 : 8
  }
  return m
})

const locationScheduledHoursPerDay = computed(() =>
  Object.values(locationAssetShiftMap.value).reduce((s, h) => s + h, 0)
)

const locationMonthlyDowntime = computed(() =>
  analysisMonths.value.map(({ year, month }) =>
    +locationDowntimes.value
      .filter(d => {
        const dt = new Date(d.start_date ?? d.log_date ?? '')
        return dt.getFullYear() === year && dt.getMonth() === month
      })
      .reduce((s, d) => s + (d.downtime_hours ?? 0), 0)
      .toFixed(1)
  )
)

const locationMonthlyAvailability = computed(() =>
  analysisMonths.value.map(({ year, month }, idx) => {
    const scheduled = workingDaysInMonth(year, month) * locationScheduledHoursPerDay.value
    if (!scheduled) return 100
    const dt = locationMonthlyDowntime.value[idx]
    return +Math.max(0, ((scheduled - dt) / scheduled) * 100).toFixed(1)
  })
)

const locationLifetimeDowntime = computed(() =>
  locationDowntimes.value.reduce((s, d) => s + (d.downtime_hours ?? 0), 0)
)

const locationCostWO = computed(() =>
  locationWorkOrders.value.reduce((s, w) => s + (w.actual_cost ?? 0), 0)
)

const locationCostInv = computed(() =>
  locationInvoices.value.reduce((s, i) => s + (i.subtotal ?? 0), 0)
)

const locationWoByType = computed(() =>
  ['corrective', 'preventative', 'predictive', 'inspection', 'project']
    .map(t => ({
      type: t,
      count: locationWorkOrders.value.filter(w => w.typ === t).length,
      cost: locationWorkOrders.value.filter(w => w.typ === t).reduce((s, w) => s + (w.actual_cost ?? 0), 0),
      hours: locationWorkOrders.value.filter(w => w.typ === t).reduce((s, w) => s + (w.actual_hours ?? 0), 0),
    }))
    .filter(t => t.count > 0)
)

const locationWoOpen = computed(() =>
  locationWorkOrders.value.filter(w => openWOStatuses.includes(w.status)).length
)
const locationWoCompleted = computed(() =>
  locationWorkOrders.value.filter(w => w.status === 'completed' || w.status === 'closed').length
)

const locationHasBalers = computed(() =>
  locationAssets.value.some(a => a.category === 'baler')
)

const locationBalesStats = computed(() => {
  if (!locationHasBalers.value) return null
  const balerIds = new Set(locationAssets.value.filter(a => a.category === 'baler').map(a => a.asset_id))
  return calcBales(locationDowntimes.value.filter(d => d.asset_id && balerIds.has(d.asset_id)))
})

const locationAvg12mAvailability = computed(() => {
  const vals = locationMonthlyAvailability.value
  if (!vals.length) return 100
  return +(vals.reduce((s, v) => s + v, 0) / vals.length).toFixed(1)
})

function locTypLabel(typ: string) {
  return typ === 'depot' ? 'Depot' : 'Redemption Centre'
}
</script>

<template>
  <div class="space-y-5">

    <!-- ── Tab bar ────────────────────────────────────────────────── -->
    <div class="flex gap-0 border-b border-slate-200">
      <button
        class="border-b-2 px-5 py-2.5 text-sm font-medium transition-colors"
        :class="activeReportTab === 'reports' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'"
        @click="activeReportTab = 'reports'"
      >Reports</button>
      <button
        class="border-b-2 px-5 py-2.5 text-sm font-medium transition-colors"
        :class="activeReportTab === 'asset' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'"
        @click="activeReportTab = 'asset'"
      >Asset Analysis</button>
      <button
        class="border-b-2 px-5 py-2.5 text-sm font-medium transition-colors"
        :class="activeReportTab === 'location' ? 'border-blue-500 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'"
        @click="activeReportTab = 'location'"
      >Location Analysis</button>
    </div>

    <!-- ═══════════════════════════════════════════════════════════ -->
    <!-- Reports tab                                                 -->
    <!-- ═══════════════════════════════════════════════════════════ -->
    <template v-if="activeReportTab === 'reports'">

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

    </template>

    <!-- ═══════════════════════════════════════════════════════════ -->
    <!-- Asset Analysis tab                                          -->
    <!-- ═══════════════════════════════════════════════════════════ -->
    <template v-else-if="activeReportTab === 'asset'">

      <!-- Asset selector -->
      <div class="flex items-center gap-4">
        <UIcon name="i-heroicons-wrench-screwdriver" class="h-5 w-5 shrink-0 text-slate-400" />
        <div class="w-full max-w-sm">
          <USelect
            v-model="selectedAssetId"
            :items="assetSelectOptions"
            placeholder="Select an asset…"
            class="w-full"
          />
        </div>
        <p v-if="selectedAssetObj" class="text-xs text-slate-400">
          {{ assetDowntimes.length }} downtime events · {{ assetWorkOrders.length }} work orders
        </p>
      </div>

      <!-- Empty state -->
      <div v-if="!selectedAssetId" class="flex flex-col items-center gap-3 rounded-xl border border-dashed border-slate-200 bg-white py-20 text-slate-400">
        <UIcon name="i-heroicons-chart-bar-square" class="h-10 w-10" />
        <p class="text-sm font-medium">Select an asset above to view its analysis</p>
        <p class="text-xs">Downtime history, availability trend, lifetime cost and work order breakdown</p>
      </div>

      <!-- Asset detail panels -->
      <template v-else-if="selectedAssetObj">

        <!-- ── Asset header card ─────────────────────────────────── -->
        <div class="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
          <div class="flex items-start gap-5 border-b border-slate-100 px-6 py-5">
            <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-600">
              <UIcon name="i-heroicons-wrench-screwdriver" class="h-6 w-6 text-white" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <h2 class="text-lg font-bold text-slate-900">{{ selectedAssetObj.asset_id }}</h2>
                <UBadge v-if="selectedAssetObj.alias" color="neutral" variant="soft" size="sm">{{ selectedAssetObj.alias }}</UBadge>
                <UBadge :color="assetStatusColor(selectedAssetObj.status)" variant="soft" size="sm" class="capitalize">{{ selectedAssetObj.status.replace('_', ' ') }}</UBadge>
                <UBadge color="neutral" variant="outline" size="sm" class="capitalize">{{ selectedAssetObj.category }}</UBadge>
              </div>
              <p class="mt-0.5 text-sm text-slate-500">{{ selectedAssetObj.manufacturer }}{{ selectedAssetObj.model_no ? ' · ' + selectedAssetObj.model_no : '' }}{{ selectedAssetObj.yr ? ' · ' + selectedAssetObj.yr : '' }}</p>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-x-6 gap-y-3 px-6 py-4 sm:grid-cols-4">
            <div v-if="selectedAssetObj.serial_no">
              <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400">Serial No</p>
              <p class="mt-0.5 text-sm text-slate-700">{{ selectedAssetObj.serial_no }}</p>
            </div>
            <div>
              <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400">Ownership</p>
              <p class="mt-0.5 text-sm capitalize text-slate-700">{{ selectedAssetObj.owned }}</p>
            </div>
            <div v-if="selectedAssetObj.date_in_service">
              <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400">In Service</p>
              <p class="mt-0.5 text-sm text-slate-700">{{ selectedAssetObj.date_in_service }}</p>
            </div>
            <div v-if="selectedAssetObj.location_id">
              <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400">Location</p>
              <p class="mt-0.5 text-sm text-slate-700">{{ locationMap[selectedAssetObj.location_id] ?? selectedAssetObj.location_id }}</p>
            </div>
            <div v-if="selectedAssetModel?.bale_time" class="sm:col-span-2">
              <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400">Bale Specs</p>
              <p class="mt-0.5 text-sm text-slate-700">{{ selectedAssetModel.bale_time }} min/bale · {{ selectedAssetModel.bale_weight }} lb/bale</p>
            </div>
            <div v-if="selectedAssetObj.notes" class="sm:col-span-4">
              <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400">Notes</p>
              <p class="mt-0.5 text-sm text-slate-600">{{ selectedAssetObj.notes }}</p>
            </div>
          </div>
        </div>

        <!-- ── KPI cards ─────────────────────────────────────────── -->
        <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <!-- Lifetime WO cost -->
          <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <p class="text-xs font-medium text-slate-500">Lifetime WO Cost</p>
            <p class="mt-1.5 text-2xl font-bold text-slate-900">{{ fmtCurrency(lifetimeCostWO) }}</p>
            <p class="mt-1 text-xs text-slate-400">{{ assetWorkOrders.length }} work orders total</p>
          </div>
          <!-- Invoice spend -->
          <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <p class="text-xs font-medium text-slate-500">Invoice Spend</p>
            <p class="mt-1.5 text-2xl font-bold text-slate-900">{{ fmtCurrency(lifetimeCostInv) }}</p>
            <p class="mt-1 text-xs text-slate-400">{{ assetInvoices.length }} invoices linked</p>
          </div>
          <!-- Lifetime downtime -->
          <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <p class="text-xs font-medium text-slate-500">Lifetime Downtime</p>
            <p class="mt-1.5 text-2xl font-bold text-slate-900">{{ lifetimeDowntimeHrs.toFixed(1) }}<span class="ml-0.5 text-sm font-medium text-slate-400">h</span></p>
            <p class="mt-1 text-xs text-slate-400">{{ assetDowntimes.length }} events recorded</p>
          </div>
          <!-- 12m avg availability -->
          <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <p class="text-xs font-medium text-slate-500">12m Avg Availability</p>
            <p class="mt-1.5 text-2xl font-bold" :class="avg12mAvailability >= 90 ? 'text-green-600' : avg12mAvailability >= 75 ? 'text-amber-600' : 'text-red-600'">
              {{ avg12mAvailability }}%
            </p>
            <p class="mt-1 text-xs text-slate-400">{{ assetShiftHours }}h/day scheduled</p>
          </div>
        </div>

        <!-- ── Charts row ─────────────────────────────────────────── -->
        <div class="grid grid-cols-1 gap-5 lg:grid-cols-2">

          <!-- Downtime history -->
          <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <h3 class="mb-4 text-sm font-semibold text-slate-900">Downtime History — Last 12 Months</h3>
            <ClientOnly>
              <apexchart
                type="bar"
                height="220"
                :options="dtBarOpts"
                :series="[{ name: 'Downtime Hours', data: assetMonthlyDowntime }]"
              />
            </ClientOnly>
          </div>

          <!-- Availability trend -->
          <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <h3 class="mb-4 text-sm font-semibold text-slate-900">Availability Trend — Last 12 Months</h3>
            <ClientOnly>
              <apexchart
                type="line"
                height="220"
                :options="availLineOpts"
                :series="[{ name: 'Availability %', data: assetMonthlyAvailability }]"
              />
            </ClientOnly>
          </div>

        </div>

        <!-- ── Bottom row: WO summary + baler ────────────────────── -->
        <div class="grid grid-cols-1 gap-5" :class="isBaler ? 'lg:grid-cols-2' : ''">

          <!-- Work order summary -->
          <div class="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
            <div class="border-b border-slate-100 px-5 py-4">
              <h3 class="text-sm font-semibold text-slate-900">Work Order Summary</h3>
              <p class="mt-0.5 text-xs text-slate-400">
                {{ woOpen }} open · {{ woCompleted }} completed
              </p>
            </div>
            <div v-if="woByType.length" class="divide-y divide-slate-50">
              <div
                v-for="row in woByType"
                :key="row.type"
                class="flex items-center gap-4 px-5 py-3"
              >
                <UBadge :color="woTypeColor(row.type)" variant="soft" size="sm" class="w-28 shrink-0 capitalize justify-center">
                  {{ row.type }}
                </UBadge>
                <div class="flex-1 text-sm text-slate-700">
                  {{ row.count }} WO{{ row.count !== 1 ? 's' : '' }}
                </div>
                <div class="text-right text-sm">
                  <p class="font-medium text-slate-900">{{ fmtCurrency(row.cost) }}</p>
                  <p class="text-xs text-slate-400">{{ row.hours.toFixed(0) }}h</p>
                </div>
              </div>
            </div>
            <div v-else class="flex flex-col items-center gap-2 py-10 text-slate-400">
              <UIcon name="i-heroicons-clipboard-document-list" class="h-7 w-7" />
              <p class="text-sm">No work orders recorded for this asset</p>
            </div>
          </div>

          <!-- Baler performance (balers only) -->
          <div v-if="isBaler && assetBalesStats" class="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
            <div class="border-b border-slate-100 px-5 py-4">
              <h3 class="text-sm font-semibold text-slate-900">Baler Performance</h3>
              <p class="mt-0.5 text-xs text-slate-400">Lifetime bale loss from downtime events</p>
            </div>
            <div class="space-y-4 px-5 py-5">
              <div class="flex items-center justify-between rounded-lg bg-amber-50 px-4 py-4">
                <div class="flex items-center gap-3">
                  <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-100">
                    <UIcon name="i-heroicons-cube" class="h-5 w-5 text-amber-600" />
                  </div>
                  <div>
                    <p class="text-xs font-medium uppercase tracking-wide text-amber-700">Lifetime Bales Lost</p>
                    <p class="mt-0.5 text-2xl font-bold text-amber-900">{{ assetBalesStats.bales.toLocaleString() }}</p>
                  </div>
                </div>
              </div>
              <div class="flex items-center justify-between rounded-lg bg-red-50 px-4 py-4">
                <div class="flex items-center gap-3">
                  <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-red-100">
                    <UIcon name="i-heroicons-banknotes" class="h-5 w-5 text-red-600" />
                  </div>
                  <div>
                    <p class="text-xs font-medium uppercase tracking-wide text-red-700">Estimated Value Lost</p>
                    <p class="mt-0.5 text-2xl font-bold text-red-900">{{ fmtCurrency(assetBalesStats.value) }}</p>
                  </div>
                </div>
              </div>
              <p class="text-xs text-slate-400">Calculated using historical commodity rates at each downtime event date.</p>
            </div>
          </div>

        </div>

      </template>
    </template>

    <!-- ═══════════════════════════════════════════════════════════ -->
    <!-- Location Analysis tab                                       -->
    <!-- ═══════════════════════════════════════════════════════════ -->
    <template v-else-if="activeReportTab === 'location'">

      <!-- Location selector -->
      <div class="flex items-center gap-4">
        <UIcon name="i-heroicons-map-pin" class="h-5 w-5 shrink-0 text-slate-400" />
        <div class="w-full max-w-sm">
          <USelect
            v-model="selectedLocationId"
            :items="locationSelectOptions"
            placeholder="Select a location…"
            class="w-full"
          />
        </div>
        <p v-if="selectedLocationObj" class="text-xs text-slate-400">
          {{ locationAssets.length }} asset{{ locationAssets.length !== 1 ? 's' : '' }} ·
          {{ locationDowntimes.length }} downtime events ·
          {{ locationWorkOrders.length }} work orders
        </p>
      </div>

      <!-- Empty state -->
      <div v-if="!selectedLocationId" class="flex flex-col items-center gap-3 rounded-xl border border-dashed border-slate-200 bg-white py-20 text-slate-400">
        <UIcon name="i-heroicons-building-office-2" class="h-10 w-10" />
        <p class="text-sm font-medium">Select a location above to view combined asset performance</p>
        <p class="text-xs">Downtime history, availability trend, lifetime cost and work order breakdown across all assets</p>
      </div>

      <!-- Location detail panels -->
      <template v-else-if="selectedLocationObj">

        <!-- ── Location header card ──────────────────────────────── -->
        <div class="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
          <div class="flex items-start gap-5 border-b border-slate-100 px-6 py-5">
            <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-indigo-600">
              <UIcon name="i-heroicons-map-pin" class="h-6 w-6 text-white" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <h2 class="text-lg font-bold text-slate-900">{{ selectedLocationObj.name }}</h2>
                <UBadge color="neutral" variant="soft" size="sm">{{ locTypLabel(selectedLocationObj.typ) }}</UBadge>
              </div>
              <p class="mt-0.5 text-sm text-slate-500">{{ selectedLocationObj.parish }}</p>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-x-6 gap-y-3 px-6 py-4 sm:grid-cols-4">
            <div>
              <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400">Supervisor</p>
              <p class="mt-0.5 text-sm text-slate-700">{{ selectedLocationObj.supervisor }}</p>
            </div>
            <div>
              <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400">Contact</p>
              <p class="mt-0.5 text-sm text-slate-700">{{ selectedLocationObj.contact_no }}</p>
            </div>
            <div>
              <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400">Total Assets</p>
              <p class="mt-0.5 text-sm text-slate-700">{{ locationAssets.length }}</p>
            </div>
            <div>
              <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400">Active Assets</p>
              <p class="mt-0.5 text-sm text-slate-700">{{ locationAssets.filter(a => a.status === 'operational').length }}</p>
            </div>
          </div>
        </div>

        <!-- ── KPI cards ─────────────────────────────────────────── -->
        <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <p class="text-xs font-medium text-slate-500">Lifetime WO Cost</p>
            <p class="mt-1.5 text-2xl font-bold text-slate-900">{{ fmtCurrency(locationCostWO) }}</p>
            <p class="mt-1 text-xs text-slate-400">{{ locationWorkOrders.length }} work orders total</p>
          </div>
          <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <p class="text-xs font-medium text-slate-500">Invoice Spend</p>
            <p class="mt-1.5 text-2xl font-bold text-slate-900">{{ fmtCurrency(locationCostInv) }}</p>
            <p class="mt-1 text-xs text-slate-400">{{ locationInvoices.length }} invoices linked</p>
          </div>
          <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <p class="text-xs font-medium text-slate-500">Lifetime Downtime</p>
            <p class="mt-1.5 text-2xl font-bold text-slate-900">{{ locationLifetimeDowntime.toFixed(1) }}<span class="ml-0.5 text-sm font-medium text-slate-400">h</span></p>
            <p class="mt-1 text-xs text-slate-400">{{ locationDowntimes.length }} events recorded</p>
          </div>
          <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <p class="text-xs font-medium text-slate-500">12m Avg Availability</p>
            <p class="mt-1.5 text-2xl font-bold" :class="locationAvg12mAvailability >= 90 ? 'text-green-600' : locationAvg12mAvailability >= 75 ? 'text-amber-600' : 'text-red-600'">
              {{ locationAvg12mAvailability }}%
            </p>
            <p class="mt-1 text-xs text-slate-400">Combined across {{ locationAssets.length }} assets</p>
          </div>
        </div>

        <!-- ── Charts ────────────────────────────────────────────── -->
        <div class="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <h3 class="mb-4 text-sm font-semibold text-slate-900">Combined Downtime — Last 12 Months</h3>
            <ClientOnly>
              <apexchart type="bar" height="220" :options="dtBarOpts" :series="[{ name: 'Downtime Hours', data: locationMonthlyDowntime }]" />
            </ClientOnly>
          </div>
          <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <h3 class="mb-4 text-sm font-semibold text-slate-900">Combined Availability — Last 12 Months</h3>
            <ClientOnly>
              <apexchart type="line" height="220" :options="availLineOpts" :series="[{ name: 'Availability %', data: locationMonthlyAvailability }]" />
            </ClientOnly>
          </div>
        </div>

        <!-- ── WO summary + baler ─────────────────────────────────── -->
        <div class="grid grid-cols-1 gap-5" :class="locationHasBalers ? 'lg:grid-cols-2' : ''">

          <!-- Work order summary -->
          <div class="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
            <div class="border-b border-slate-100 px-5 py-4">
              <h3 class="text-sm font-semibold text-slate-900">Work Order Summary</h3>
              <p class="mt-0.5 text-xs text-slate-400">{{ locationWoOpen }} open · {{ locationWoCompleted }} completed</p>
            </div>
            <div v-if="locationWoByType.length" class="divide-y divide-slate-50">
              <div v-for="row in locationWoByType" :key="row.type" class="flex items-center gap-4 px-5 py-3">
                <UBadge :color="woTypeColor(row.type)" variant="soft" size="sm" class="w-28 shrink-0 capitalize justify-center">{{ row.type }}</UBadge>
                <div class="flex-1 text-sm text-slate-700">{{ row.count }} WO{{ row.count !== 1 ? 's' : '' }}</div>
                <div class="text-right text-sm">
                  <p class="font-medium text-slate-900">{{ fmtCurrency(row.cost) }}</p>
                  <p class="text-xs text-slate-400">{{ row.hours.toFixed(0) }}h</p>
                </div>
              </div>
            </div>
            <div v-else class="flex flex-col items-center gap-2 py-10 text-slate-400">
              <UIcon name="i-heroicons-clipboard-document-list" class="h-7 w-7" />
              <p class="text-sm">No work orders recorded for this location</p>
            </div>
          </div>

          <!-- Baler performance (locations with balers) -->
          <div v-if="locationHasBalers && locationBalesStats" class="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
            <div class="border-b border-slate-100 px-5 py-4">
              <h3 class="text-sm font-semibold text-slate-900">Baler Performance</h3>
              <p class="mt-0.5 text-xs text-slate-400">
                {{ locationAssets.filter(a => a.category === 'baler').length }} baler{{ locationAssets.filter(a => a.category === 'baler').length !== 1 ? 's' : '' }} at this location — lifetime bale loss
              </p>
            </div>
            <div class="space-y-4 px-5 py-5">
              <div class="flex items-center rounded-lg bg-amber-50 px-4 py-4">
                <div class="flex items-center gap-3">
                  <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-100">
                    <UIcon name="i-heroicons-cube" class="h-5 w-5 text-amber-600" />
                  </div>
                  <div>
                    <p class="text-xs font-medium uppercase tracking-wide text-amber-700">Lifetime Bales Lost</p>
                    <p class="mt-0.5 text-2xl font-bold text-amber-900">{{ locationBalesStats.bales.toLocaleString() }}</p>
                  </div>
                </div>
              </div>
              <div class="flex items-center rounded-lg bg-red-50 px-4 py-4">
                <div class="flex items-center gap-3">
                  <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-red-100">
                    <UIcon name="i-heroicons-banknotes" class="h-5 w-5 text-red-600" />
                  </div>
                  <div>
                    <p class="text-xs font-medium uppercase tracking-wide text-red-700">Estimated Value Lost</p>
                    <p class="mt-0.5 text-2xl font-bold text-red-900">{{ fmtCurrency(locationBalesStats.value) }}</p>
                  </div>
                </div>
              </div>
              <p class="text-xs text-slate-400">Calculated using historical commodity rates at each downtime event date.</p>
            </div>
          </div>

        </div>

        <!-- ── Asset list at location ─────────────────────────────── -->
        <div class="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
          <div class="border-b border-slate-100 px-5 py-4">
            <h3 class="text-sm font-semibold text-slate-900">Assets at this Location</h3>
          </div>
          <div class="divide-y divide-slate-50">
            <button
              v-for="asset in locationAssets"
              :key="asset.asset_id"
              class="flex w-full items-center gap-4 px-5 py-3 text-left transition-colors hover:bg-blue-50"
              @click="selectedAssetId = asset.asset_id; activeReportTab = 'asset'"
            >
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-slate-900">{{ asset.asset_id }}<span v-if="asset.alias" class="ml-1.5 text-xs font-normal text-slate-400">{{ asset.alias }}</span></p>
                <p class="text-xs text-slate-400 capitalize">{{ asset.manufacturer }}{{ asset.model_no ? ' · ' + asset.model_no : '' }} · {{ asset.category }}</p>
              </div>
              <UBadge :color="assetStatusColor(asset.status)" variant="soft" size="sm" class="capitalize shrink-0">{{ asset.status.replace('_', ' ') }}</UBadge>
              <UIcon name="i-heroicons-arrow-right" class="h-4 w-4 shrink-0 text-slate-300" />
            </button>
          </div>
        </div>

      </template>
    </template>

  </div>
</template>
