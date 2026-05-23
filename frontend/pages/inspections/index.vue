<script setup lang="ts">
import type { Inspection } from "~/types"

const { getAll, remove } = useInspections()

const { data: inspections, refresh } = await useAsyncData("inspections", () => getAll())

const resultColors: Record<string, string> = { pass: "success", fail: "error", na: "neutral" }

const columns = [
  { accessorKey: "id", header: "ID" },
  { accessorKey: "inspection_no", header: "Inspection No" },
  { accessorKey: "asset_id", header: "Asset" },
  { accessorKey: "inspection_date", header: "Date" },
  { accessorKey: "overall_result", header: "Result" },
  { accessorKey: "submitted", header: "Submitted" },
  { id: "actions", header: "" },
]

const search = ref("")
const resultFilter = ref<string | null>(null)

const resultOptions = [
  { label: "All", value: null },
  { label: "Pass", value: "pass" },
  { label: "Fail", value: "fail" },
  { label: "N/A", value: "na" },
]

const filtered = computed(() =>
  (inspections.value ?? []).filter((i) => {
    const q = search.value.toLowerCase()
    const matchSearch = !q || (i.asset_id ?? "").toLowerCase().includes(q) || i.inspection_no.toLowerCase().includes(q)
    const matchResult = !resultFilter.value || i.overall_result === resultFilter.value
    return matchSearch && matchResult
  })
)

const deleteTarget = ref<Inspection | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value?.id) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.id)
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
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Inspections</h1>
      <UButton to="/inspections/new" leading-icon="i-heroicons-plus">New Inspection</UButton>
    </div>

    <UCard>
      <template #header>
        <div class="flex flex-wrap items-center gap-3">
          <UInput
            v-model="search"
            placeholder="Search by asset or inspection no..."
            leading-icon="i-heroicons-magnifying-glass"
            class="max-w-xs"
          />
          <USelect
            v-model="resultFilter"
            :items="resultOptions"
            placeholder="Filter by result"
            class="w-40"
          />
        </div>
      </template>

      <UTable :data="filtered" :columns="columns">
        <template #overall_result-cell="{ row }">
          <UBadge :color="resultColors[row.overall_result] ?? 'neutral'" variant="soft">
            {{ row.overall_result }}
          </UBadge>
        </template>
        <template #submitted-cell="{ row }">
          <UBadge :color="row.submitted ? 'success' : 'neutral'" variant="soft" size="sm">
            {{ row.submitted ? "Submitted" : "Draft" }}
          </UBadge>
        </template>
        <template #asset_id-cell="{ row }">
          <NuxtLink :to="`/assets/${row.asset_id}`" class="text-primary-600 hover:underline dark:text-primary-400">
            {{ row.asset_id }}
          </NuxtLink>
        </template>
        <template #actions-cell="{ row }">
          <div class="flex items-center gap-1">
            <UButton :to="`/inspections/${row.id}`" variant="ghost" size="xs" icon="i-heroicons-pencil" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Inspection</h3></template>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Delete inspection <strong>{{ deleteTarget?.inspection_no }}</strong>? This cannot be undone.
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
