<script setup lang="ts">
import type { Asset, WorkOrder, Downtime, AssetPM } from "~/types"

const { get } = useApi()

const { data: assets } = await useAsyncData("assets", () => get<Asset[]>("/assets"))
const { data: workOrders } = await useAsyncData("work-orders", () => get<WorkOrder[]>("/work-orders"))
const { data: downtimes } = await useAsyncData("downtimes", () => get<Downtime[]>("/downtimes"))
const { data: assetPMs } = await useAsyncData("asset-pms", () => get<AssetPM[]>("/maintenance/asset-pms"))

// ── Status colour maps ─────────────────────────────────────────
const statusColors: Record<string, string> = {
  operational: "success", maintenance: "warning", out_of_service: "error", disposed: "neutral",
}
const woStatusColors: Record<string, string> = {
  requested: "info", in_progress: "warning", completed: "success", on_hold: "neutral", cancelled: "error",
}

// ── Asset stats ────────────────────────────────────────────────
const assetsByStatus = computed(() => {
  const counts: Record<string, number> = {}
  for (const a of assets.value ?? []) counts[a.status] = (counts[a.status] ?? 0) + 1
  return counts
})

const assetsDown = computed(() =>
  (assets.value ?? []).filter((a) => a.status === "out_of_service" || a.status === "maintenance").length
)

// Availability: (total possible hrs - downtime hrs in last 30d) / total possible hrs
const availability = computed(() => {
  const now = new Date()
  const cutoff = new Date(now)
  cutoff.setDate(now.getDate() - 30)

  const recentDowntimeHrs = (downtimes.value ?? [])
    .filter((d) => {
      const date = new Date(d.start_date ?? d.log_date ?? "")
      return date >= cutoff
    })
    .reduce((sum, d) => sum + (d.downtime_hours ?? 0), 0)

  const activeAssets = (assets.value ?? []).filter((a) => a.status !== "disposed").length
  if (!activeAssets) return 100
  const possible = activeAssets * 30 * 24
  return Math.max(0, +((1 - recentDowntimeHrs / possible) * 100).toFixed(1))
})

// ── Work order stats ───────────────────────────────────────────
const openWorkOrders = computed(() =>
  (workOrders.value ?? []).filter((w) => !["completed", "closed", "cancelled"].includes(w.status))
)

const workOrdersByStatus = computed(() => {
  const counts: Record<string, number> = {}
  for (const w of openWorkOrders.value) counts[w.status] = (counts[w.status] ?? 0) + 1
  return counts
})

const totalDowntimeHours = computed(() =>
  (downtimes.value ?? []).reduce((sum, d) => sum + (d.downtime_hours ?? 0), 0)
)

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
  { label: "Downtime Hours",     value: totalDowntimeHours.value.toFixed(1), suffix: "h", icon: "i-heroicons-exclamation-triangle",   color: "text-orange-500", bg: "bg-orange-50" },
  { label: "PMs Due (30 days)",  value: pmsDueSoon.value.length,            suffix: "",   icon: "i-heroicons-calendar-days",          color: "text-purple-500", bg: "bg-purple-50" },
])

// ── MTTR / MTBF trend (last 6 months) ─────────────────────────
function getLast6Months() {
  const now = new Date()
  return Array.from({ length: 6 }, (_, i) => {
    const d = new Date(now.getFullYear(), now.getMonth() - (5 - i), 1)
    return {
      year: d.getFullYear(),
      month: d.getMonth(),
      label: d.toLocaleString("default", { month: "short", year: "2-digit" }),
      daysInMonth: new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate(),
    }
  })
}

const last6Months = getLast6Months()
const monthLabels = last6Months.map((m) => m.label)

// MTTR = average downtime hours per failure event, per month
const mttrSeries = computed(() => [{
  name: "MTTR",
  data: last6Months.map(({ year, month }) => {
    const events = (downtimes.value ?? []).filter((d) => {
      const date = new Date(d.start_date ?? d.log_date ?? "")
      return date.getFullYear() === year && date.getMonth() === month && (d.downtime_hours ?? 0) > 0
    })
    if (!events.length) return 0
    const total = events.reduce((s, e) => s + (e.downtime_hours ?? 0), 0)
    return +(total / events.length).toFixed(2)
  }),
}])

// MTBF = (calendar hours in month - downtime hours) / failure events
const mtbfSeries = computed(() => [{
  name: "MTBF",
  data: last6Months.map(({ year, month, daysInMonth }) => {
    const events = (downtimes.value ?? []).filter((d) => {
      const date = new Date(d.start_date ?? d.log_date ?? "")
      return date.getFullYear() === year && date.getMonth() === month
    })
    if (!events.length) return 0
    const totalDowntime = events.reduce((s, e) => s + (e.downtime_hours ?? 0), 0)
    const operatingHrs = daysInMonth * 24 - totalDowntime
    return +(operatingHrs / events.length).toFixed(2)
  }),
}])

function areaChartOptions(color: string, unit: string) {
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
    fill: {
      type: "gradient",
      gradient: { shadeIntensity: 1, opacityFrom: 0.25, opacityTo: 0.02, stops: [0, 95, 100] },
    },
    xaxis: {
      categories: monthLabels,
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

const mttrOptions = areaChartOptions("#3b82f6", "h")
const mtbfOptions = areaChartOptions("#8b5cf6", "h")

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
      </div>
    </div>

    <!-- MTTR / MTBF Trend Charts -->
    <div class="grid grid-cols-1 gap-5 lg:grid-cols-2">
      <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div class="mb-1 flex items-center justify-between">
          <div>
            <h2 class="text-sm font-semibold text-slate-700">MTTR — Mean Time to Repair</h2>
            <p class="text-xs text-slate-400">Average downtime hours per failure event</p>
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
        <div class="space-y-3">
          <div v-for="(count, status) in assetsByStatus" :key="status" class="flex items-center justify-between">
            <UBadge :color="statusColors[status] ?? 'neutral'" variant="soft">{{ status.replace(/_/g, " ") }}</UBadge>
            <div class="flex items-center gap-3">
              <div class="h-1.5 w-28 overflow-hidden rounded-full bg-slate-100">
                <div class="h-full rounded-full bg-blue-500" :style="{ width: `${(count / (assets?.length ?? 1)) * 100}%` }" />
              </div>
              <span class="w-5 text-right text-sm font-semibold text-slate-600">{{ count }}</span>
            </div>
          </div>
          <p v-if="!assets?.length" class="text-sm text-slate-400">No assets found.</p>
        </div>
      </div>

      <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 class="mb-4 text-sm font-semibold text-slate-700">Open Work Orders by Status</h2>
        <div class="space-y-3">
          <div v-for="(count, status) in workOrdersByStatus" :key="status" class="flex items-center justify-between">
            <UBadge :color="woStatusColors[status] ?? 'neutral'" variant="soft">{{ status.replace(/_/g, " ") }}</UBadge>
            <span class="text-sm font-semibold text-slate-600">{{ count }}</span>
          </div>
          <p v-if="!openWorkOrders.length" class="text-sm text-slate-400">No open work orders.</p>
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
