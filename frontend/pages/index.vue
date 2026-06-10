<script setup lang="ts">
import type { Asset, WorkOrder, Downtime, AssetPM } from "~/types"

const { get } = useApi()

const { data: assets } = await useAsyncData("assets", () => get<Asset[]>("/assets"))
const { data: workOrders } = await useAsyncData("work-orders", () => get<WorkOrder[]>("/work-orders"))
const { data: downtimes } = await useAsyncData("downtimes", () => get<Downtime[]>("/downtimes"))
const { data: assetPMs } = await useAsyncData("asset-pms", () => get<AssetPM[]>("/maintenance/asset-pms"))

const statusColors: Record<string, string> = {
  operational: "success",
  maintenance: "warning",
  out_of_service: "error",
  disposed: "neutral",
}

const woStatusColors: Record<string, string> = {
  requested: "info",
  in_progress: "warning",
  completed: "success",
  on_hold: "neutral",
  cancelled: "error",
}

const assetsByStatus = computed(() => {
  const counts: Record<string, number> = {}
  for (const a of assets.value ?? []) {
    counts[a.status] = (counts[a.status] ?? 0) + 1
  }
  return counts
})

const openWorkOrders = computed(() =>
  (workOrders.value ?? []).filter((w) => !["completed", "closed", "cancelled"].includes(w.status))
)

const workOrdersByStatus = computed(() => {
  const counts: Record<string, number> = {}
  for (const w of openWorkOrders.value) {
    counts[w.status] = (counts[w.status] ?? 0) + 1
  }
  return counts
})

const totalDowntimeHours = computed(() =>
  (downtimes.value ?? []).reduce((sum, d) => sum + (d.downtime_hours ?? 0), 0)
)

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

const kpiCards = computed(() => [
  { label: "Total Assets", value: assets.value?.length ?? 0, icon: "i-heroicons-wrench-screwdriver", color: "text-blue-500" },
  { label: "Open Work Orders", value: openWorkOrders.value.length, icon: "i-heroicons-clipboard-document-list", color: "text-amber-500" },
  { label: "Downtime Hours", value: totalDowntimeHours.value.toFixed(1), icon: "i-heroicons-exclamation-triangle", color: "text-red-500" },
  { label: "PMs Due (30 days)", value: pmsDueSoon.value.length, icon: "i-heroicons-calendar-days", color: "text-purple-500" },
])

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
]
</script>

<template>
  <div class="space-y-6">

    <!-- KPI Cards -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div
        v-for="card in kpiCards"
        :key="card.label"
        class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200"
      >
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ card.label }}</p>
            <p class="mt-2 text-3xl font-bold text-slate-900">{{ card.value }}</p>
          </div>
          <div class="rounded-lg bg-white p-2.5">
            <UIcon :name="card.icon" class="h-5 w-5" :class="card.color" />
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-5 lg:grid-cols-2">
      <!-- Assets by Status -->
      <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 class="mb-4 text-sm font-semibold text-slate-700">Assets by Status</h2>
        <div class="space-y-3">
          <div
            v-for="(count, status) in assetsByStatus"
            :key="status"
            class="flex items-center justify-between"
          >
            <UBadge :color="statusColors[status] ?? 'neutral'" variant="soft">
              {{ status.replace(/_/g, " ") }}
            </UBadge>
            <div class="flex items-center gap-3">
              <div class="h-1.5 w-28 overflow-hidden rounded-full bg-slate-100">
                <div
                  class="h-full rounded-full bg-blue-500"
                  :style="{ width: `${(count / (assets?.length ?? 1)) * 100}%` }"
                />
              </div>
              <span class="w-5 text-right text-sm font-semibold text-slate-600">{{ count }}</span>
            </div>
          </div>
          <p v-if="!assets?.length" class="text-sm text-slate-400">No assets found.</p>
        </div>
      </div>

      <!-- Open Work Orders by Status -->
      <div class="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h2 class="mb-4 text-sm font-semibold text-slate-700">Open Work Orders by Status</h2>
        <div class="space-y-3">
          <div
            v-for="(count, status) in workOrdersByStatus"
            :key="status"
            class="flex items-center justify-between"
          >
            <UBadge :color="woStatusColors[status] ?? 'neutral'" variant="soft">
              {{ status.replace(/_/g, " ") }}
            </UBadge>
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
        <UButton to="/work-orders" variant="ghost" size="sm" trailing-icon="i-heroicons-arrow-right" color="neutral">
          View all
        </UButton>
      </div>
      <UTable :data="recentWorkOrders" :columns="woColumns">
        <template #status-cell="{ row: { original: row } }">
          <UBadge :color="woStatusColors[row.status] ?? 'neutral'" variant="soft">
            {{ row.status.replace(/_/g, " ") }}
          </UBadge>
        </template>
        <template #priority-cell="{ row: { original: row } }">
          <UBadge :color="row.priority === 'High' ? 'error' : row.priority === 'Medium' ? 'warning' : 'neutral'" variant="soft">
            {{ row.priority }}
          </UBadge>
        </template>
      </UTable>
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
