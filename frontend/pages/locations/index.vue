<script setup lang="ts">
import type { Location } from "~/types"

const { getAll, remove } = useLocations()

const { data: locations, refresh } = await useAsyncData("locations", () => getAll())

const columns = [
  { accessorKey: "location_id", header: "ID" },
  { accessorKey: "name", header: "Name" },
  { accessorKey: "parish", header: "Parish" },
  { accessorKey: "typ", header: "Type" },
  { accessorKey: "supervisor", header: "Supervisor" },
  { accessorKey: "contact_no", header: "Contact" },
  { accessorKey: "shift_depot", header: "Shift Depot" },
  { id: "actions", header: "" },
]

const search = ref("")
const filtered = computed(() =>
  (locations.value ?? []).filter((l) => {
    const q = search.value.toLowerCase()
    return !q || l.name.toLowerCase().includes(q) || l.parish.toLowerCase().includes(q) || l.supervisor.toLowerCase().includes(q)
  })
)

const deleteTarget = ref<Location | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value?.location_id) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.location_id)
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
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Locations</h1>
      <UButton to="/locations/new" leading-icon="i-heroicons-plus">New Location</UButton>
    </div>

    <UCard>
      <template #header>
        <UInput
          v-model="search"
          placeholder="Search by name, parish or supervisor..."
          leading-icon="i-heroicons-magnifying-glass"
          class="max-w-sm"
        />
      </template>

      <UTable :data="filtered" :columns="columns">
        <template #typ-cell="{ row }">
          <UBadge :color="row.typ === 'depot' ? 'info' : 'neutral'" variant="soft" size="sm">
            {{ row.typ.replace(/_/g, " ") }}
          </UBadge>
        </template>
        <template #shift_depot-cell="{ row }">
          <UBadge v-if="row.shift_depot" color="success" variant="soft" size="sm">Yes</UBadge>
          <span v-else class="text-gray-400">—</span>
        </template>
        <template #actions-cell="{ row }">
          <div class="flex items-center gap-1">
            <UButton :to="`/locations/${row.location_id}`" variant="ghost" size="xs" icon="i-heroicons-pencil" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Location</h3></template>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Delete location <strong>{{ deleteTarget?.name }}</strong>? This cannot be undone.
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
