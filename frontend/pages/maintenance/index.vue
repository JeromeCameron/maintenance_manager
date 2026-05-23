<script setup lang="ts">
import type { AssetPM } from "~/types"

const { getAllPMs, removePM, getPlans } = useMaintenance()
const { getAll: getAssets } = useAssets()

const { data: assetPMs, refresh } = await useAsyncData("asset-pms", () => getAllPMs())
const { data: plans } = await useAsyncData("pm-plans", () => getPlans())
const { data: assets } = await useAsyncData("assets-select", () => getAssets())

const planMap = computed(() => {
  const m: Record<string, string> = {}
  for (const p of plans.value ?? []) m[p.pm_id] = p.description ?? p.pm_id
  return m
})

const assetMap = computed(() => {
  const m: Record<string, string> = {}
  for (const a of assets.value ?? []) m[a.asset_id] = `${a.asset_id} — ${a.manufacturer}`
  return m
})

const today = new Date()
const in30Days = new Date(today)
in30Days.setDate(today.getDate() + 30)

const pmsDueSoon = computed(() =>
  (assetPMs.value ?? []).filter((pm) => {
    if (!pm.next_service || !pm.active) return false
    return new Date(pm.next_service) <= in30Days
  })
)

const columns = [
  { accessorKey: "id", header: "ID" },
  { accessorKey: "asset_id", header: "Asset" },
  { accessorKey: "pm_plan_id", header: "PM Plan" },
  { accessorKey: "last_service", header: "Last Service" },
  { accessorKey: "next_service", header: "Next Service" },
  { accessorKey: "active", header: "Active" },
  { id: "actions", header: "" },
]

const activeTab = ref("all")
const tabs = [
  { label: "All PMs", value: "all" },
  { label: `Due Soon (${pmsDueSoon.value.length})`, value: "due" },
  { label: "PM Plans", value: "plans" },
]

const filtered = computed(() => {
  if (activeTab.value === "due") return pmsDueSoon.value
  return assetPMs.value ?? []
})

const deleteTarget = ref<AssetPM | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value?.id) return
  deleting.value = true
  try {
    await removePM(deleteTarget.value.id)
    await refresh()
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Maintenance</h1>
      <UButton to="/maintenance/new" leading-icon="i-heroicons-plus">New PM Schedule</UButton>
    </div>

    <!-- Due soon alert -->
    <UAlert
      v-if="pmsDueSoon.length"
      color="warning"
      variant="soft"
      icon="i-heroicons-clock"
      :title="`${pmsDueSoon.length} PM${pmsDueSoon.length > 1 ? 's' : ''} due in the next 30 days`"
    />

    <div class="flex gap-2 border-b border-gray-200 dark:border-gray-700">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        class="border-b-2 px-4 py-2 text-sm font-medium transition-colors"
        :class="activeTab === tab.value
          ? 'border-primary-500 text-primary-600 dark:text-primary-400'
          : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'"
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Asset PM table -->
    <UCard v-if="activeTab !== 'plans'">
      <UTable :data="filtered" :columns="columns">
        <template #asset_id-cell="{ row }">
          <NuxtLink :to="`/assets/${row.asset_id}`" class="text-primary-600 hover:underline dark:text-primary-400">
            {{ row.asset_id }}
          </NuxtLink>
        </template>
        <template #pm_plan_id-cell="{ row }">
          {{ planMap[row.pm_plan_id] ?? row.pm_plan_id ?? "—" }}
        </template>
        <template #active-cell="{ row }">
          <UBadge :color="row.active ? 'success' : 'neutral'" variant="soft" size="sm">
            {{ row.active ? "Active" : "Inactive" }}
          </UBadge>
        </template>
        <template #next_service-cell="{ row }">
          <span
            :class="row.next_service && new Date(row.next_service) <= in30Days
              ? 'font-semibold text-warning-600 dark:text-warning-400'
              : ''"
          >
            {{ row.next_service ?? "—" }}
          </span>
        </template>
        <template #actions-cell="{ row }">
          <div class="flex items-center gap-1">
            <UButton :to="`/maintenance/${row.id}`" variant="ghost" size="xs" icon="i-heroicons-pencil" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- PM Plans table -->
    <UCard v-else>
      <UTable
        :data="plans ?? []"
        :columns="[
          { accessorKey: 'pm_id', header: 'Plan ID' },
          { accessorKey: 'asset_type', header: 'Asset Type' },
          { accessorKey: 'trigger', header: 'Trigger' },
          { accessorKey: 'frequency', header: 'Frequency' },
          { accessorKey: 'owner', header: 'Owner' },
          { accessorKey: 'description', header: 'Description' },
        ]"
      />
    </UCard>

    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete PM Schedule</h3></template>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Delete PM schedule <strong>#{{ deleteTarget?.id }}</strong>? This cannot be undone.
          </p>
          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton variant="ghost" @click="deleteTarget = null">Cancel</UButton>
              <UButton color="error" :loading="deleting" @click="confirmDelete">Delete</UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
  </div>
</template>
