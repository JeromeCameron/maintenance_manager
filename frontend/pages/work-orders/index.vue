<script setup lang="ts">
import type { WorkOrder } from "~/types"

const { getAll, remove } = useWorkOrders()

const { data: workOrders, refresh } = await useAsyncData("work-orders", () => getAll())

const statusColors: Record<string, string> = {
  requested: "info", scheduled: "info", awaiting_parts: "warning", awaiting_po: "warning",
  in_progress: "warning", on_hold: "neutral", cancelled: "error", completed: "success", closed: "neutral",
}

const columns = [
  { accessorKey: "work_order_id", header: "WO #" },
  { accessorKey: "asset_id", header: "Asset" },
  { accessorKey: "priority", header: "Priority" },
  { accessorKey: "typ", header: "Type" },
  { accessorKey: "status", header: "Status" },
  { accessorKey: "issue_date", header: "Issued" },
  { accessorKey: "expected_date", header: "Expected" },
  { id: "actions", header: "" },
]

const search = ref("")
const statusFilter = ref<string | null>(null)

const statusOptions = [
  { label: "All", value: null },
  ...["requested", "scheduled", "awaiting_parts", "awaiting_po", "in_progress", "on_hold", "cancelled", "completed", "closed"]
    .map((s) => ({ label: s.replace(/_/g, " "), value: s })),
]

const filtered = computed(() =>
  (workOrders.value ?? []).filter((w) => {
    const matchSearch =
      !search.value ||
      String(w.work_order_id).includes(search.value) ||
      (w.asset_id ?? "").toLowerCase().includes(search.value.toLowerCase())
    const matchStatus = !statusFilter.value || w.status === statusFilter.value
    return matchSearch && matchStatus
  })
)

const deleteTarget = ref<WorkOrder | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value?.work_order_id) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.work_order_id)
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
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Work Orders</h1>
      <UButton to="/work-orders/new" leading-icon="i-heroicons-plus">New Work Order</UButton>
    </div>

    <UCard>
      <template #header>
        <div class="flex flex-wrap items-center gap-3">
          <UInput
            v-model="search"
            placeholder="Search by WO # or asset..."
            leading-icon="i-heroicons-magnifying-glass"
            class="max-w-xs"
          />
          <USelect
            v-model="statusFilter"
            :items="statusOptions"
            placeholder="Filter by status"
            class="w-48"
          />
        </div>
      </template>

      <UTable :data="filtered" :columns="columns">
        <template #status-cell="{ row }">
          <UBadge :color="statusColors[row.status] ?? 'neutral'" variant="soft">
            {{ row.status.replace(/_/g, " ") }}
          </UBadge>
        </template>
        <template #priority-cell="{ row }">
          <UBadge :color="row.priority === 'High' ? 'error' : row.priority === 'Medium' ? 'warning' : 'neutral'" variant="soft">
            {{ row.priority }}
          </UBadge>
        </template>
        <template #actions-cell="{ row }">
          <div class="flex items-center gap-1">
            <UButton :to="`/work-orders/${row.work_order_id}`" variant="ghost" size="xs" icon="i-heroicons-pencil" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Work Order</h3></template>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Delete work order <strong>#{{ deleteTarget?.work_order_id }}</strong>? This cannot be undone.
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
