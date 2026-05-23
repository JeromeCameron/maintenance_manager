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
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>

    <!-- KPI Cards -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <UCard v-for="card in kpiCards" :key="card.label">
        <div class="flex items-center gap-4">
          <div class="rounded-xl bg-gray-100 p-3 dark:bg-gray-800">
            <UIcon :name="card.icon" class="h-6 w-6" :class="card.color" />
          </div>
          <div>
            <p class="text-sm text-gray-500 dark:text-gray-400">{{ card.label }}</p>
            <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ card.value }}</p>
          </div>
        </div>
      </UCard>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <!-- Assets by Status -->
      <UCard>
        <template #header>
          <h2 class="font-semibold text-gray-900 dark:text-white">Assets by Status</h2>
        </template>
        <div class="space-y-3">
          <div
            v-for="(count, status) in assetsByStatus"
            :key="status"
            class="flex items-center justify-between"
          >
            <div class="flex items-center gap-2">
              <UBadge :color="statusColors[status] ?? 'neutral'" variant="soft">
                {{ status.replace(/_/g, " ") }}
              </UBadge>
            </div>
            <div class="flex items-center gap-3">
              <div class="h-2 w-32 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
                <div
                  class="h-full rounded-full bg-primary-500"
                  :style="{ width: `${(count / (assets?.length ?? 1)) * 100}%` }"
                />
              </div>
              <span class="w-6 text-right text-sm font-medium text-gray-700 dark:text-gray-300">{{ count }}</span>
            </div>
          </div>
          <p v-if="!assets?.length" class="text-sm text-gray-400">No assets found.</p>
        </div>
      </UCard>

      <!-- Open Work Orders by Status -->
      <UCard>
        <template #header>
          <h2 class="font-semibold text-gray-900 dark:text-white">Open Work Orders by Status</h2>
        </template>
        <div class="space-y-3">
          <div
            v-for="(count, status) in workOrdersByStatus"
            :key="status"
            class="flex items-center justify-between"
          >
            <UBadge :color="woStatusColors[status] ?? 'neutral'" variant="soft">
              {{ status.replace(/_/g, " ") }}
            </UBadge>
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300">{{ count }}</span>
          </div>
          <p v-if="!openWorkOrders.length" class="text-sm text-gray-400">No open work orders.</p>
        </div>
      </UCard>
    </div>

    <!-- Recent Open Work Orders -->
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="font-semibold text-gray-900 dark:text-white">Open Work Orders</h2>
          <UButton to="/work-orders" variant="ghost" size="sm" trailing-icon="i-heroicons-arrow-right">
            View all
          </UButton>
        </div>
      </template>
      <UTable :data="recentWorkOrders" :columns="woColumns">
        <template #status-cell="{ row }">
          <UBadge :color="woStatusColors[row.status] ?? 'neutral'" variant="soft">
            {{ row.status.replace(/_/g, " ") }}
          </UBadge>
        </template>
        <template #priority-cell="{ row }">
          <UBadge :color="row.priority === 'High' ? 'error' : row.priority === 'Medium' ? 'warning' : 'neutral'" variant="soft">
            {{ row.priority }}
          </UBadge>
        </template>
      </UTable>
    </UCard>

    <!-- PMs Due Soon -->
    <UCard v-if="pmsDueSoon.length">
      <template #header>
        <h2 class="font-semibold text-gray-900 dark:text-white">Preventative Maintenance Due (Next 30 Days)</h2>
      </template>
      <UTable
        :data="pmsDueSoon"
        :columns="[
          { accessorKey: 'asset_id', header: 'Asset' },
          { accessorKey: 'pm_plan_id', header: 'PM Plan' },
          { accessorKey: 'last_service', header: 'Last Service' },
          { accessorKey: 'next_service', header: 'Due Date' },
        ]"
      />
    </UCard>
  </div>
</template>
