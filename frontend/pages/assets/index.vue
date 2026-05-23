<script setup lang="ts">
import type { Asset } from "~/types"

const { getAll, remove } = useAssets()

const { data: assets, refresh } = await useAsyncData("assets", () => getAll())

const statusColors: Record<string, string> = {
  operational: "success",
  maintenance: "warning",
  out_of_service: "error",
  disposed: "neutral",
}

const columns = [
  { accessorKey: "asset_id", header: "Asset ID" },
  { accessorKey: "manufacturer", header: "Manufacturer" },
  { accessorKey: "category", header: "Category" },
  { accessorKey: "status", header: "Status" },
  { accessorKey: "owned", header: "Ownership" },
  { accessorKey: "location_id", header: "Location" },
  { id: "actions", header: "" },
]

const search = ref("")
const filtered = computed(() =>
  (assets.value ?? []).filter(
    (a) =>
      a.asset_id.toLowerCase().includes(search.value.toLowerCase()) ||
      a.manufacturer.toLowerCase().includes(search.value.toLowerCase())
  )
)

const deleteTarget = ref<Asset | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.asset_id)
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
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Assets</h1>
      <UButton to="/assets/new" leading-icon="i-heroicons-plus">New Asset</UButton>
    </div>

    <UCard>
      <template #header>
        <UInput
          v-model="search"
          placeholder="Search by ID or manufacturer..."
          leading-icon="i-heroicons-magnifying-glass"
          class="max-w-sm"
        />
      </template>

      <UTable :data="filtered" :columns="columns">
        <template #status-cell="{ row }">
          <UBadge :color="statusColors[row.status] ?? 'neutral'" variant="soft">
            {{ row.status.replace(/_/g, " ") }}
          </UBadge>
        </template>
        <template #category-cell="{ row }">
          <span class="capitalize">{{ row.category }}</span>
        </template>
        <template #owned-cell="{ row }">
          <span class="capitalize">{{ row.owned }}</span>
        </template>
        <template #actions-cell="{ row }">
          <div class="flex items-center gap-1">
            <UButton :to="`/assets/${row.asset_id}`" variant="ghost" size="xs" icon="i-heroicons-pencil" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Delete confirmation modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header>
            <h3 class="font-semibold">Delete Asset</h3>
          </template>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Are you sure you want to delete asset <strong>{{ deleteTarget?.asset_id }}</strong>? This cannot be undone.
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
