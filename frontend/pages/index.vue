<script setup lang="ts">
import type { Asset, WorkOrder, Downtime, AssetPM } from "~/types"

const { get } = useApi()

const { data: assets } = await useAsyncData("assets", () => get<Asset[]>("/assets"))
const { data: workOrders } = await useAsyncData("work-orders", () => get<WorkOrder[]>("/work-orders"))
const { data: downtimes } = await useAsyncData("downtimes", () => get<Downtime[]>("/downtimes"))

interface ReactivityStats { total: number; planned: number; unplanned: number; planned_pct: number; unplanned_pct: number }
interface ReactivityTrendMonth { month: string; total: number; planned: number; unplanned: number; planned_pct: number; unplanned_pct: number }
const { data: reactivity } = await useAsyncData("wo-reactivity", () => get<ReactivityStats>("/work-orders/reactivity"))
const { data: reactivityTrend } = await useAsyncData("wo-reactivity-trend", () => get<ReactivityTrendMonth[]>("/work-orders/reactivity/trend?months=6"))

interface MonthlyMetrics {
  month: string
  scheduled_hours: number
  downtime_hours: number
  num_failures: number
  mttr: number | null
  mtbf: number | null
  availability: number
}
const { data: monthlyMetrics } = await useAsyncData("downtime-metrics", () => get<MonthlyMetrics[]>("/downtimes/monthly-metrics?months=6"))
const { data: assetPMs } = await useAsyncData("asset-pms", () => get<AssetPM[]>("/maintenance/asset-pms"))

// ── Status colour maps ─────────────────────────────────────────
const statusColors: Record<string, string> = {
  operational: "success", maintenance: "warning", out_of_service: "error", disposed: "neutral",
}
const statusHex: Record<string, string> = {
  operational: "#1d4ed8", maintenance: "#3b82f6", out_of_service: "#93c5fd", disposed: "#bfdbfe",
}
const statusOrder = ["operational", "maintenance", "out_of_service", "disposed"]
const woStatusColors: Record<string, string> = {
  requested: "info", in_progress: "warning", completed: "success", on_hold: "neutral", cancelled: "error",
}

// ── Asset stats ────────────────────────────────────────────────
const assetsByStatus = computed(() => {
  const counts: Record<string, number> = {}
  for (const a of assets.value ?? []) counts[a.status] = (counts[a.status] ?? 0) + 1
  return counts
})

const assetDonutItems = computed(() =>
  statusOrder
    .filter((s) => (assetsByStatus.value[s] ?? 0) > 0)
    .map((s) => ({ status: s, count: assetsByStatus.value[s] ?? 0, color: statusHex[s] }))
)
const assetDonutSeries = computed(() => assetDonutItems.value.map((i) => i.count))
const assetDonutOptions = computed(() => ({
  chart: { type: "donut", toolbar: { show: false }, fontFamily: "inherit", animations: { enabled: true, speed: 500 } },
  colors: assetDonutItems.value.map((i) => i.color),
  labels: assetDonutItems.value.map((i) => i.status.replace(/_/g, " ")),
  plotOptions: {
    pie: {
      expandOnClick: false,
      donut: {
        size: "70%",
        labels: {
          show: true,
          value: { fontSize: "26px", fontWeight: 700, color: "#0f172a", offsetY: 4 },
          total: {
            show: true,
            label: "Assets",
            fontSize: "11px",
            fontWeight: 500,
            color: "#94a3b8",
            formatter: () => String(assets.value?.length ?? 0),
          },
        },
      },
    },
  },
  dataLabels: { enabled: false },
  stroke: { width: 3, colors: ["#ffffff"] },
  legend: { show: false },
  tooltip: { y: { formatter: (v: number) => `${v} asset${v !== 1 ? "s" : ""}` } },
}))

const assetsDown = computed(() =>
  (assets.value ?? []).filter((a) => a.status === "out_of_service" || a.status === "maintenance").length
)

const currentMonthMetrics = computed(() => {
  const key = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`
  return monthlyMetrics.value?.find((m) => m.month === key) ?? null
})

// Availability for the current month from backend metrics
const availability = computed(() => currentMonthMetrics.value?.availability ?? 100)

// ── Work order stats ───────────────────────────────────────────
const openWorkOrders = computed(() =>
  (workOrders.value ?? []).filter((w) => !["completed", "closed", "cancelled"].includes(w.status))
)

const workOrdersByStatus = computed(() => {
  const counts: Record<string, number> = {}
  for (const w of openWorkOrders.value) counts[w.status] = (counts[w.status] ?? 0) + 1
  return counts
})


const reactivityGaugeSeries = computed(() => [reactivity.value?.unplanned_pct ?? 0])
const reactivityGaugeOptions = computed(() => ({
  chart: { type: "radialBar", toolbar: { show: false }, fontFamily: "inherit", sparkline: { enabled: true } },
  plotOptions: {
    radialBar: {
      startAngle: -135,
      endAngle: 135,
      hollow: { size: "60%" },
      track: { background: "#f1f5f9", strokeWidth: "100%", margin: 0 },
      dataLabels: {
        name: { show: true, fontSize: "10px", fontWeight: 500, color: "#94a3b8", offsetY: 18 },
        value: { show: true, fontSize: "20px", fontWeight: 700, color: "#0f172a", offsetY: -8,
          formatter: (v: number) => `${Math.round(v)}%` },
      },
    },
  },
  fill: {
    type: "gradient",
    gradient: { shade: "light", type: "horizontal", gradientToColors: ["#ef4444"], stops: [0, 100] },
  },
  colors: ["#22c55e"],
  labels: ["Unplanned"],
  stroke: { lineCap: "round" },
}))

const trendMonthLabels = computed(() =>
  (reactivityTrend.value ?? []).map(({ month }) => {
    const [y, m] = month.split("-").map(Number)
    return new Date(y, m - 1, 1).toLocaleString("default", { month: "short", year: "2-digit" })
  })
)

const trendSeries = computed(() => [
  { name: "Planned",   data: (reactivityTrend.value ?? []).map((m) => m.planned) },
  { name: "Unplanned", data: (reactivityTrend.value ?? []).map((m) => m.unplanned) },
])

const trendChartOptions = computed(() => ({
  chart: { type: "bar", stacked: true, toolbar: { show: false }, fontFamily: "inherit", animations: { enabled: true, speed: 400 } },
  plotOptions: { bar: { columnWidth: "50%", borderRadius: 3 } },
  colors: ["#3b82f6", "#fbbf24"],
  xaxis: {
    categories: trendMonthLabels.value,
    labels: { style: { fontSize: "11px", colors: "#94a3b8" } },
    axisBorder: { show: false },
    axisTicks: { show: false },
  },
  yaxis: {
    labels: { style: { fontSize: "11px", colors: "#94a3b8" }, formatter: (v: number) => String(Math.round(v)) },
    min: 0,
  },
  grid: { borderColor: "#f1f5f9", strokeDashArray: 4, padding: { left: 4, right: 4 } },
  dataLabels: { enabled: false },
  legend: { show: false },
  tooltip: {
    shared: true,
    y: { formatter: (v: number) => String(Math.round(v)) },
  },
}))

const now = new Date()
const prevMonthDate = new Date(now.getFullYear(), now.getMonth() - 1, 1)
const prevMonthKey = `${prevMonthDate.getFullYear()}-${String(prevMonthDate.getMonth() + 1).padStart(2, "0")}`
const prevMonthLabel = prevMonthDate.toLocaleString("default", { month: "long" })

const currentMonthDowntimeHours = computed(() => currentMonthMetrics.value?.downtime_hours ?? 0)
const prevMonthDowntimeHours = computed(() => monthlyMetrics.value?.find((m) => m.month === prevMonthKey)?.downtime_hours ?? 0)

// ── PMs due ────────────────────────────────────────────────────
const pmsDueSoon = computed(() => {
  const today = new Date()
  const in30Days = new Date(today)
  in30Days.setDate(today.getDate() + 30)
  return (assetPMs.value ?? []).filter((pm) => {
    if (!pm.next_service) return false
    const next = new Date(pm.next_service)
    return next <= in30Days && pm.active
  })
})

// ── KPI cards ──────────────────────────────────────────────────
const kpiCards = computed(() => [
  { label: "Total Assets",       value: assets.value?.length ?? 0,         suffix: "",   icon: "i-heroicons-wrench-screwdriver",     color: "text-blue-500",   bg: "bg-blue-50" },
  { label: "Assets Down",        value: assetsDown.value,                   suffix: "",   icon: "i-heroicons-x-circle",               color: "text-red-500",    bg: "bg-red-50" },
  { label: "Availability (30d)", value: availability.value,                 suffix: "%",  icon: "i-heroicons-check-circle",           color: "text-green-500",  bg: "bg-green-50" },
  { label: "Open Work Orders",   value: openWorkOrders.value.length,        suffix: "",   icon: "i-heroicons-clipboard-document-list", color: "text-amber-500", bg: "bg-amber-50" },
  { label: "Unplanned Downtime (this month)", value: currentMonthDowntimeHours.value.toFixed(1), suffix: "h", icon: "i-heroicons-exclamation-triangle", color: "text-orange-500", bg: "bg-orange-50", caption: `${prevMonthLabel}: ${prevMonthDowntimeHours.value.toFixed(1)}h` },
  { label: "PMs Due (30 days)",  value: pmsDueSoon.value.length,            suffix: "",   icon: "i-heroicons-calendar-days",          color: "text-purple-500", bg: "bg-purple-50" },
])

// ── MTTR / MTBF trend (last 6 months) ─────────────────────────
const monthLabels = computed(() =>
  (monthlyMetrics.value ?? []).map(({ month }) => {
    const [y, m] = month.split("-").map(Number)
    return new Date(y, m - 1, 1).toLocaleString("default", { month: "short", year: "2-digit" })
  })
)

const mttrSeries = computed(() => [{
  name: "MTTR",
  data: (monthlyMetrics.value ?? []).map((m) => m.mttr),
}])

const mtbfSeries = computed(() => [{
  name: "MTBF",
  data: (monthlyMetrics.value ?? []).map((m) => m.mtbf),
}])

function areaChartOptions(color: string, unit: string, labels: string[]) {
  return {
    chart: {
      type: "area",
      height: 170,
      toolbar: { show: false },
      zoom: { enabled: false },
      fontFamily: "inherit",
      animations: { enabled: true, speed: 400 },
    },
    stroke: { curve: "smooth", width: 2 },
    connectNulls: false,
    fill: {
      type: "gradient",
      gradient: { shadeIntensity: 1, opacityFrom: 0.25, opacityTo: 0.02, stops: [0, 95, 100] },
    },
    xaxis: {
      categories: labels,
      labels: { style: { fontSize: "11px", colors: "#94a3b8" } },
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    yaxis: {
      labels: {
        style: { fontSize: "11px", colors: "#94a3b8" },
        formatter: (v: number) => v.toFixed(1) + unit,
      },
      min: 0,
    },
    grid: { borderColor: "#f1f5f9", strokeDashArray: 4, padding: { left: 4, right: 4 } },
    colors: [color],
    dataLabels: { enabled: false },
    markers: { size: 3, strokeWidth: 0 },
    tooltip: { y: { formatter: (v: number) => v.toFixed(1) + " hrs" } },
  }
}

const mttrOptions = computed(() => areaChartOptions("#3b82f6", "h", monthLabels.value))
const mtbfOptions = computed(() => areaChartOptions("#8b5cf6", "h", monthLabels.value))

// ── Recent work orders table ───────────────────────────────────
const recentWorkOrders = computed(() =>
  [...(workOrders.value ?? [])]
    .filter((w) => !["completed", "closed"].includes(w.status))
    .slice(0, 8)
)

const woColumns = [
  { accessorKey: "work_order_id", header: "WO #" },
  { accessorKey: "asset_id", header: "Asset" },
  { accessorKey: "priority", header: "Priority" },
  { accessorKey: "typ", header: "Type" },
  { accessorKey: "status", header: "Status" },
  { id: "actions", header: "" },
]

const selectedWoId = ref<number | null>(null)
const showWoModal = ref(false)

function openWorkOrder(id: number) {
  selectedWoId.value = id
  showWoModal.value = true
}
</script>

<template>
  <div class="space-y-6">

    <!-- KPI Cards -->
    <div class="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
      <div
        v-for="card in kpiCards"
        :key="card.label"
        class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200"
      >
        <div class="flex items-start justify-between">
          <div class="min-w-0 flex-1">
            <p class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ card.label }}</p>
            <p class="mt-2 text-3xl font-bold text-slate-900">
              {{ card.value }}<span v-if="card.suffix" class="text-lg font-semibold text-slate-400">{{ card.suffix }}</span>
            </p>
          </div>
          <div :class="['rounded-lg p-2.5', card.bg]">
            <UIcon :name="card.icon" class="h-5 w-5 shrink-0" :class="card.color" />
          </div>
        </div>
        <p v-if="card.caption" class="mt-2 text-xs text-slate-400">{{ card.caption }}</p>
      </div>
    </div>

    <!-- MTTR / MTBF Trend Charts -->
    <div class="grid grid-cols-1 gap-5 lg:grid-cols-2">
      <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div class="mb-1 flex items-center justify-between">
          <div>
            <h2 class="text-sm font-semibold text-slate-700">MTTR — Mean Time to Repair</h2>
            <p class="text-xs text-slate-400">Average downtime hours per failure event</p>
            <p class="mt-0.5 text-xs font-medium text-green-600">Lower is better</p>
          </div>
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50">
            <UIcon name="i-heroicons-wrench" class="h-4 w-4 text-blue-500" />
          </div>
        </div>
        <ClientOnly>
          <apexchart type="area" height="170" :options="mttrOptions" :series="mttrSeries" />
          <template #fallback>
            <div class="flex h-[170px] items-center justify-center text-sm text-slate-400">Loading chart…</div>
          </template>
        </ClientOnly>
      </div>

      <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div class="mb-1 flex items-center justify-between">
          <div>
            <h2 class="text-sm font-semibold text-slate-700">MTBF — Mean Time Between Failures</h2>
            <p class="text-xs text-slate-400">Operating hours between failure events</p>
            <p class="mt-0.5 text-xs font-medium text-green-600">Higher is better</p>
          </div>
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-50">
            <UIcon name="i-heroicons-chart-bar" class="h-4 w-4 text-purple-500" />
          </div>
        </div>
        <ClientOnly>
          <apexchart type="area" height="170" :options="mtbfOptions" :series="mtbfSeries" />
          <template #fallback>
            <div class="flex h-[170px] items-center justify-center text-sm text-slate-400">Loading chart…</div>
          </template>
        </ClientOnly>
      </div>
    </div>

    <!-- Assets by Status / Open Work Orders -->
    <div class="grid grid-cols-1 gap-5 lg:grid-cols-2">
      <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 class="mb-4 text-sm font-semibold text-slate-700">Assets by Status</h2>
        <div class="flex items-center gap-6">
          <!-- Donut -->
          <div class="shrink-0 w-[180px]">
            <ClientOnly>
              <apexchart type="donut" height="180" :options="assetDonutOptions" :series="assetDonutSeries" />
              <template #fallback>
                <div class="flex h-[180px] items-center justify-center text-sm text-slate-400">Loading…</div>
              </template>
            </ClientOnly>
          </div>
          <!-- Legend -->
          <div class="flex-1 space-y-3">
            <div v-for="item in assetDonutItems" :key="item.status" class="flex items-center gap-3">
              <span class="h-2.5 w-2.5 shrink-0 rounded-full" :style="{ background: item.color }" />
              <span class="flex-1 text-sm capitalize text-slate-600">{{ item.status.replace(/_/g, " ") }}</span>
              <span class="text-sm font-bold text-slate-900">{{ Math.round((item.count / (assets?.length ?? 1)) * 100) }}%</span>
              <span class="w-6 text-right text-xs text-slate-400">{{ item.count }}</span>
            </div>
            <p v-if="!assets?.length" class="text-sm text-slate-400">No assets found.</p>
          </div>
        </div>
      </div>

      <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div class="mb-1 flex items-center justify-between">
          <div>
            <h2 class="text-sm font-semibold text-slate-700">Reactivity Trend</h2>
            <p class="text-xs text-slate-400">Planned vs unplanned work orders — last 6 months</p>
          </div>
          <div class="flex items-center gap-3 text-xs text-slate-500">
            <span class="flex items-center gap-1.5"><span class="inline-block h-2 w-2 rounded-full bg-blue-500" />Planned</span>
            <span class="flex items-center gap-1.5"><span class="inline-block h-2 w-2 rounded-full bg-amber-400" />Unplanned</span>
          </div>
        </div>

        <ClientOnly>
          <apexchart type="bar" height="170" :options="trendChartOptions" :series="trendSeries" />
          <template #fallback>
            <div class="flex h-[170px] items-center justify-center text-sm text-slate-400">Loading chart…</div>
          </template>
        </ClientOnly>

        <!-- All-time gauge -->
        <div v-if="reactivity?.total" class="mt-2 border-t border-slate-100 pt-3">
          <p class="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">All time</p>
          <div class="flex items-center gap-4">
            <div class="w-[120px] shrink-0">
              <ClientOnly>
                <apexchart type="radialBar" height="120" :options="reactivityGaugeOptions" :series="reactivityGaugeSeries" />
              </ClientOnly>
            </div>
            <div class="flex-1 grid grid-cols-3 gap-2">
              <div class="rounded-lg bg-slate-50 px-3 py-2 text-center">
                <p class="text-lg font-bold text-slate-900">{{ reactivity.total }}</p>
                <p class="text-[10px] uppercase tracking-wide text-slate-400">Total</p>
              </div>
              <div class="rounded-lg bg-blue-50 px-3 py-2 text-center">
                <p class="text-lg font-bold text-blue-700">{{ reactivity.planned }}</p>
                <p class="text-[10px] uppercase tracking-wide text-blue-400">Planned</p>
              </div>
              <div class="rounded-lg bg-amber-50 px-3 py-2 text-center">
                <p class="text-lg font-bold text-amber-700">{{ reactivity.unplanned }}</p>
                <p class="text-[10px] uppercase tracking-wide text-amber-400">Unplanned</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Open Work Orders -->
    <div class="rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
      <div class="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <h2 class="text-sm font-semibold text-slate-700">Open Work Orders</h2>
        <UButton to="/work-orders" variant="ghost" size="sm" trailing-icon="i-heroicons-arrow-right" color="neutral">View all</UButton>
      </div>
      <UTable :data="recentWorkOrders" :columns="woColumns">
        <template #status-cell="{ row: { original: row } }">
          <UBadge :color="woStatusColors[row.status] ?? 'neutral'" variant="soft">{{ row.status.replace(/_/g, " ") }}</UBadge>
        </template>
        <template #priority-cell="{ row: { original: row } }">
          <UBadge :color="row.priority === 'High' ? 'error' : row.priority === 'Medium' ? 'warning' : 'neutral'" variant="soft">{{ row.priority }}</UBadge>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <UButton variant="ghost" size="xs" icon="i-heroicons-eye" @click="openWorkOrder(row.work_order_id)" />
        </template>
      </UTable>

      <WorkOrderModal v-model:open="showWoModal" :work-order-id="selectedWoId" />
    </div>

    <!-- PMs Due Soon -->
    <div v-if="pmsDueSoon.length" class="rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
      <div class="flex items-center gap-2 border-b border-slate-100 px-5 py-4">
        <UIcon name="i-heroicons-clock" class="h-4 w-4 text-amber-500" />
        <h2 class="text-sm font-semibold text-slate-700">Preventative Maintenance Due (Next 30 Days)</h2>
      </div>
      <UTable
        :data="pmsDueSoon"
        :columns="[
          { accessorKey: 'asset_id', header: 'Asset' },
          { accessorKey: 'pm_plan_id', header: 'PM Plan' },
          { accessorKey: 'last_service', header: 'Last Service' },
          { accessorKey: 'next_service', header: 'Due Date' },
        ]"
      />
    </div>

  </div>
</template>
