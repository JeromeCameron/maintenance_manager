<script setup lang="ts">
import type { WorkOrder } from "~/types"

const { getAll, create, remove } = useWorkOrders()
const { getAll: getAssets } = useAssets()

const { data: workOrders, refresh } = await useAsyncData("work-orders", () => getAll())
const { data: assets } = await useAsyncData("assets-select", () => getAssets())

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

// ── Create modal ──────────────────────────────────────────────
const showCreateModal = ref(false)

const defaultForm = (): Partial<WorkOrder> => ({
  status: "requested",
  priority: "Low",
  typ: "corrective",
  issue_date: new Date().toISOString().slice(0, 10),
})

const form = ref<Partial<WorkOrder>>(defaultForm())
const saving = ref(false)
const formError = ref<string | null>(null)

const assetOptions = computed(() =>
  (assets.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id }))
)

const priorityOptions = ["Low", "Medium", "High"]
const typeOptions = ["corrective", "predictive", "preventative", "inspection", "project"]
const woStatusOptions = ["requested", "scheduled", "awaiting_parts", "awaiting_po", "in_progress", "on_hold"]

function onModalOpen(isOpen: boolean) {
  if (isOpen) {
    form.value = defaultForm()
    formError.value = null
  }
}

async function submitCreate() {
  saving.value = true
  formError.value = null
  try {
    await create(form.value as WorkOrder)
    await refresh()
    showCreateModal.value = false
  } catch (e: unknown) {
    formError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    saving.value = false
  }
}

// ── Delete modal ──────────────────────────────────────────────
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
      <h1 class="text-2xl font-bold text-slate-900">Work Orders</h1>
      <UModal v-model:open="showCreateModal" @update:open="onModalOpen">
        <UButton leading-icon="i-heroicons-plus">New Work Order</UButton>
        <template #content>
          <div class="w-full max-w-2xl rounded-xl bg-white shadow-xl dark:bg-gray-900">

            <!-- Modal header -->
            <div class="flex items-start gap-4 border-b border-gray-100 px-6 py-5 dark:border-gray-800">
              <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50 dark:bg-primary-950">
                <UIcon name="i-heroicons-clipboard-document-list" class="h-5 w-5 text-primary-500" />
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="text-base font-semibold text-slate-900">New Work Order</h3>
                <p class="mt-0.5 text-sm text-gray-500 dark:text-gray-400">Fill in the details to create a new work order</p>
              </div>
              <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showCreateModal = false" />
            </div>

            <!-- Form body -->
            <div class="px-6 py-5 space-y-6">

              <!-- Asset -->
              <UFormField label="Asset" class="w-full">
                <USelect v-model="form.asset_id" :items="assetOptions" placeholder="Select asset…" class="w-full" />
              </UFormField>

              <!-- Classification -->
              <div>
                <div class="mb-3 flex items-center gap-3">
                  <span class="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Classification</span>
                  <div class="flex-1 border-t border-gray-100 dark:border-gray-800" />
                </div>
                <div class="grid grid-cols-2 gap-x-5 gap-y-4">
                  <UFormField label="Priority">
                    <USelect v-model="form.priority" :items="priorityOptions" class="w-full" />
                  </UFormField>
                  <UFormField label="Type">
                    <USelect v-model="form.typ" :items="typeOptions" class="w-full" />
                  </UFormField>
                </div>
              </div>

              <!-- Schedule -->
              <div>
                <div class="mb-3 flex items-center gap-3">
                  <span class="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Schedule</span>
                  <div class="flex-1 border-t border-gray-100 dark:border-gray-800" />
                </div>
                <div class="grid grid-cols-2 gap-x-5 gap-y-4">
                  <UFormField label="Status">
                    <USelect v-model="form.status" :items="woStatusOptions" class="w-full" />
                  </UFormField>
                  <UFormField label="Issue Date">
                    <UInput v-model="form.issue_date" type="date" class="w-full" />
                  </UFormField>
                  <UFormField label="Expected Date">
                    <UInput v-model="form.expected_date" type="date" class="w-full" />
                  </UFormField>
                </div>
              </div>

              <!-- Estimates -->
              <div>
                <div class="mb-3 flex items-center gap-3">
                  <span class="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Estimates</span>
                  <div class="flex-1 border-t border-gray-100 dark:border-gray-800" />
                </div>
                <div class="grid grid-cols-2 gap-x-5 gap-y-4">
                  <UFormField label="Estimated Hours">
                    <UInput v-model.number="form.estimated_hours" type="number" step="0.5" placeholder="0" class="w-full" />
                  </UFormField>
                  <UFormField label="Estimated Cost ($)">
                    <UInput v-model.number="form.estimated_cost" type="number" step="0.01" placeholder="0.00" class="w-full" />
                  </UFormField>
                </div>
              </div>

              <!-- Details -->
              <div>
                <div class="mb-3 flex items-center gap-3">
                  <span class="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Details</span>
                  <div class="flex-1 border-t border-gray-100 dark:border-gray-800" />
                </div>
                <div class="space-y-4">
                  <UFormField label="Description" class="w-full">
                    <UTextarea v-model="form.description" :rows="3" placeholder="Describe the issue or work to be done…" class="w-full" />
                  </UFormField>
                  <UFormField label="Notes" class="w-full">
                    <UTextarea v-model="form.notes" :rows="2" placeholder="Any additional notes…" class="w-full" />
                  </UFormField>
                </div>
              </div>

              <UAlert v-if="formError" color="error" variant="soft" :description="formError" />
            </div>

            <!-- Footer -->
            <div class="flex items-center justify-end gap-3 border-t border-gray-100 px-6 py-4 dark:border-gray-800">
              <UButton variant="ghost" color="neutral" @click="showCreateModal = false">Cancel</UButton>
              <UButton :loading="saving" leading-icon="i-heroicons-check" @click="submitCreate">
                Create Work Order
              </UButton>
            </div>

          </div>
        </template>
      </UModal>
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
        <template #status-cell="{ row: { original: row } }">
          <UBadge :color="statusColors[row.status] ?? 'neutral'" variant="soft">
            {{ row.status.replace(/_/g, " ") }}
          </UBadge>
        </template>
        <template #priority-cell="{ row: { original: row } }">
          <UBadge :color="row.priority === 'High' ? 'error' : row.priority === 'Medium' ? 'warning' : 'neutral'" variant="soft">
            {{ row.priority }}
          </UBadge>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton :to="`/work-orders/${row.work_order_id}`" variant="ghost" size="xs" icon="i-heroicons-pencil" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Delete confirmation modal -->
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
