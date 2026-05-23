<script setup lang="ts">
import type { Downtime } from "~/types"

const { getAll, remove, getCauses } = useDowntime()

const { data: downtimes, refresh } = await useAsyncData("downtimes", () => getAll())
const { data: causes } = await useAsyncData("downtime-causes", () => getCauses())

const causeMap = computed(() => {
  const m: Record<number, string> = {}
  for (const c of causes.value ?? []) {
    if (c.cause_id != null) m[c.cause_id] = c.name
  }
  return m
})

const columns = [
  { accessorKey: "downtime_id", header: "ID" },
  { accessorKey: "asset_id", header: "Asset" },
  { accessorKey: "cause_id", header: "Cause" },
  { accessorKey: "start_date", header: "Start" },
  { accessorKey: "end_date", header: "End" },
  { accessorKey: "downtime_hours", header: "Hours" },
  { accessorKey: "planned", header: "Planned" },
  { id: "actions", header: "" },
]

const search = ref("")
const filtered = computed(() =>
  (downtimes.value ?? []).filter((d) => {
    if (!search.value) return true
    const q = search.value.toLowerCase()
    return (
      (d.asset_id ?? "").toLowerCase().includes(q) ||
      String(d.downtime_id).includes(q) ||
      (d.work_order ?? "").toLowerCase().includes(q)
    )
  })
)

const totalHours = computed(() =>
  (downtimes.value ?? []).reduce((s, d) => s + (d.downtime_hours ?? 0), 0)
)

const deleteTarget = ref<Downtime | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value?.downtime_id) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.downtime_id)
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
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Downtime</h1>
      <div class="flex items-center gap-3">
        <div class="rounded-lg bg-red-50 px-4 py-2 text-sm dark:bg-red-950">
          <span class="text-red-600 dark:text-red-400">Total: </span>
          <span class="font-bold text-red-700 dark:text-red-300">{{ totalHours.toFixed(1) }}h</span>
        </div>
        <UButton to="/downtime/new" leading-icon="i-heroicons-plus">Log Downtime</UButton>
      </div>
    </div>

    <UCard>
      <template #header>
        <UInput
          v-model="search"
          placeholder="Search by asset or WO..."
          leading-icon="i-heroicons-magnifying-glass"
          class="max-w-sm"
        />
      </template>

      <UTable :data="filtered" :columns="columns">
        <template #cause_id-cell="{ row }">
          {{ causeMap[row.cause_id] ?? row.cause_id ?? "—" }}
        </template>
        <template #planned-cell="{ row }">
          <UBadge :color="row.planned ? 'info' : 'error'" variant="soft" size="sm">
            {{ row.planned ? "Planned" : "Unplanned" }}
          </UBadge>
        </template>
        <template #downtime_hours-cell="{ row }">
          <span class="font-medium">{{ row.downtime_hours?.toFixed(1) ?? "—" }}h</span>
        </template>
        <template #actions-cell="{ row }">
          <div class="flex items-center gap-1">
            <UButton :to="`/downtime/${row.downtime_id}`" variant="ghost" size="xs" icon="i-heroicons-pencil" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Downtime Record</h3></template>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Delete downtime record <strong>#{{ deleteTarget?.downtime_id }}</strong>? This cannot be undone.
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
