<script setup lang="ts">
import type { WorkOrder, AssetPM } from "~/types"

const { isAdmin } = useAuth()
const { getAll, create, remove, update } = useWorkOrders()
const { getAll: getAssets } = useAssets()
const { getAll: getSuppliers } = useSuppliers()
const { getPMsByAsset } = useMaintenance()

const { data: workOrders, refresh } = await useAsyncData("work-orders", () => getAll())
const [{ data: assets }, { data: suppliers }] = await Promise.all([
  useAsyncData("assets-select", () => getAssets()),
  useAsyncData("suppliers-select", () => getSuppliers()),
])

// ── Lookups ───────────────────────────────────────────────────
const supplierMap = computed(() =>
  Object.fromEntries((suppliers.value ?? []).map((s) => [s.supplier_id, s.name]))
)

const statusStyles: Record<string, string> = {
  requested:      "bg-blue-50 text-blue-600 ring-1 ring-blue-200",
  scheduled:      "bg-indigo-50 text-indigo-600 ring-1 ring-indigo-200",
  awaiting_parts: "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
  awaiting_po:    "bg-orange-50 text-orange-600 ring-1 ring-orange-200",
  in_progress:    "bg-yellow-50 text-yellow-700 ring-1 ring-yellow-200",
  on_hold:        "bg-slate-100 text-slate-500 ring-1 ring-slate-200",
  cancelled:      "bg-red-50 text-red-500 ring-1 ring-red-200",
  completed:      "bg-green-50 text-green-600 ring-1 ring-green-200",
  closed:         "bg-emerald-50 text-emerald-600 ring-1 ring-emerald-200",
}

const typeStyles: Record<string, string> = {
  corrective:   "bg-red-50 text-red-600",
  predictive:   "bg-purple-50 text-purple-600",
  preventative: "bg-teal-50 text-teal-700",
  inspection:   "bg-sky-50 text-sky-600",
  project:      "bg-indigo-50 text-indigo-600",
}

// ── Filters ───────────────────────────────────────────────────
const search = ref("")
const statusFilter = ref<string | null>(null)
const priorityFilter = ref<string | null>(null)

const statusOptions = [
  { label: "All statuses", value: null },
  ...["requested", "scheduled", "awaiting_parts", "awaiting_po", "in_progress", "on_hold", "cancelled", "completed", "closed"]
    .map((s) => ({ label: s.replace(/_/g, " "), value: s })),
]

const filterPriorityOptions = [
  { label: "All priorities", value: null },
  { label: "High", value: "High" },
  { label: "Medium", value: "Medium" },
  { label: "Low", value: "Low" },
]

const DONE_STATUSES = ["completed", "closed", "cancelled"]

const filtered = computed(() =>
  (workOrders.value ?? [])
    .filter((w) => {
      const matchSearch =
        !search.value ||
        String(w.work_order_id).includes(search.value) ||
        (w.asset_id ?? "").toLowerCase().includes(search.value.toLowerCase()) ||
        (w.description ?? "").toLowerCase().includes(search.value.toLowerCase())
      const matchStatus = !statusFilter.value || w.status === statusFilter.value
      const matchPriority = !priorityFilter.value || w.priority === priorityFilter.value
      return matchSearch && matchStatus && matchPriority
    })
    .sort((a, b) => (b.issue_date ?? "").localeCompare(a.issue_date ?? ""))
)

const filteredTodo = computed(() => filtered.value.filter((w) => !DONE_STATUSES.includes(w.status)))
const filteredDone = computed(() => filtered.value.filter((w) => DONE_STATUSES.includes(w.status)))

// ── Tabs ──────────────────────────────────────────────────────
const activeTab = ref("todo")
const tabs = computed(() => [
  { value: "todo", slot: "todo", label: `To Do (${filteredTodo.value.length})` },
  { value: "done", slot: "done", label: `Done (${filteredDone.value.length})` },
])

// ── Helpers ───────────────────────────────────────────────────
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const [year, month, day] = value.slice(0, 10).split('-').map(Number)
  if (!year || !month || !day) return '—'
  return `${String(day).padStart(2,'0')}-${MONTHS[month - 1]}-${String(year).slice(-2)}`
}

function isOverdue(wo: WorkOrder): boolean {
  if (!wo.expected_date) return false
  if (DONE_STATUSES.includes(wo.status)) return false
  return wo.expected_date < new Date().toISOString().slice(0, 10)
}

async function quickStatusChange(wo: WorkOrder, newStatus: string) {
  await update(wo.work_order_id!, { ...wo, status: newStatus as WorkOrder["status"] })
  await refresh()
}

// ── Form options ──────────────────────────────────────────────
const priorityOptions = ["Low", "Medium", "High"]
const typeOptions = ["corrective", "predictive", "preventative", "inspection", "project"]
const plannedOptions = [
  { label: "Planned", value: true },
  { label: "Unplanned", value: false },
]
const woStatusOptions = ["requested", "scheduled", "awaiting_parts", "awaiting_po", "in_progress", "on_hold", "cancelled", "completed", "closed"]

const assetOptions = computed(() =>
  (assets.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id }))
)
const supplierOptions = computed(() =>
  [{ label: "None", value: undefined }, ...(suppliers.value ?? []).map((s) => ({ label: s.name, value: s.supplier_id }))]
)

// ── PM logic (create only) ────────────────────────────────────
const createAssetPMs = ref<AssetPM[]>([])

async function loadPMsForAsset(assetId: string | undefined) {
  createAssetPMs.value = assetId ? (await getPMsByAsset(assetId) ?? []) : []
}

const createPMOptions = computed(() =>
  [{ label: "None", value: undefined }, ...createAssetPMs.value.map((p) => ({ label: `${p.pm_plan_id} — next: ${p.next_service ?? "—"}`, value: p.id }))]
)

// ── Create modal ──────────────────────────────────────────────
const showCreateModal = ref(false)
const defaultForm = (): Partial<WorkOrder> => ({
  status: "requested",
  priority: "Low",
  typ: "corrective",
  issue_date: new Date().toISOString().slice(0, 10),
})
const createForm = ref<Partial<WorkOrder>>(defaultForm())
const savingCreate = ref(false)
const createError = ref<string | null>(null)

watch(() => createForm.value.asset_id, (id) => {
  createForm.value.asset_pm_id = undefined
  loadPMsForAsset(id)
})

function onCreateOpen(isOpen: boolean) {
  if (isOpen) {
    // Ensure the edit modal can't also be showing (and won't overwrite this form
    // if a previous edit's fetch resolves late) before opening the create modal.
    showEditModal.value = false
    editingId.value = null
    createForm.value = defaultForm()
    createError.value = null
    createAssetPMs.value = []
  }
}

function openCreate() {
  showCreateModal.value = true
}

async function submitCreate() {
  savingCreate.value = true
  createError.value = null
  try {
    await create(createForm.value as WorkOrder)
    await refresh()
    showCreateModal.value = false
  } catch (e: unknown) {
    createError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingCreate.value = false
  }
}

// ── Edit modal ────────────────────────────────────────────────
const showEditModal = ref(false)
const editingId = ref<number | null>(null)

function openEdit(wo: WorkOrder) {
  showCreateModal.value = false
  editingId.value = wo.work_order_id!
  showEditModal.value = true
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
  <div class="flex min-h-full flex-col gap-4">
    <UModal v-model:open="showCreateModal" :ui="{ content: 'max-w-2xl' }" @update:open="onCreateOpen">
      <template #content>
          <div class="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-xl bg-white shadow-xl">
            <!-- Header -->
            <div class="flex shrink-0 items-start gap-4 border-b border-gray-100 px-6 py-5">
              <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50">
                <UIcon name="i-heroicons-clipboard-document-list" class="h-5 w-5 text-primary-500" />
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="text-base font-semibold text-slate-900">New Work Order</h3>
                <p class="mt-0.5 text-sm text-gray-500">Fill in the details to create a new work order</p>
              </div>
              <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showCreateModal = false" />
            </div>

            <!-- Scrollable body -->
            <div class="flex-1 overflow-y-auto px-6 py-5 space-y-5">
              <div class="grid grid-cols-2 gap-x-5 gap-y-4">
                <UFormField label="Asset" class="col-span-2">
                  <USelect v-model="createForm.asset_id" :items="assetOptions" placeholder="Select asset…" class="w-full" />
                </UFormField>
                <UFormField label="Supplier">
                  <USelect v-model="createForm.supplier_id" :items="supplierOptions" placeholder="Select supplier…" class="w-full" />
                </UFormField>
                <UFormField v-if="createForm.asset_id" label="PM Plan">
                  <USelect v-model="createForm.asset_pm_id" :items="createPMOptions" placeholder="Link to PM (optional)" class="w-full" />
                </UFormField>
                <UFormField label="Priority">
                  <USelect v-model="createForm.priority" :items="priorityOptions" class="w-full" />
                </UFormField>
                <UFormField label="Type">
                  <USelect v-model="createForm.typ" :items="typeOptions" class="w-full" />
                </UFormField>
                <UFormField label="Planned / Unplanned">
                  <USelect v-model="createForm.planned" :items="plannedOptions" placeholder="Select…" class="w-full" />
                </UFormField>
                <UFormField label="Status">
                  <USelect v-model="createForm.status" :items="woStatusOptions" class="w-full" />
                </UFormField>
                <UFormField label="Issue Date">
                  <UInput v-model="createForm.issue_date" type="date" class="w-full" />
                </UFormField>
                <UFormField label="Expected Date">
                  <UInput v-model="createForm.expected_date" type="date" class="w-full" />
                </UFormField>
                <UFormField label="Estimated Hours">
                  <UInput v-model.number="createForm.estimated_hours" type="number" step="0.5" class="w-full" />
                </UFormField>
                <UFormField label="Estimated Cost ($)">
                  <UInput v-model.number="createForm.estimated_cost" type="number" step="0.01" class="w-full" />
                </UFormField>
                <UFormField label="Description" class="col-span-2">
                  <UTextarea v-model="createForm.description" :rows="3" class="w-full" />
                </UFormField>
                <UFormField label="Notes" class="col-span-2">
                  <UTextarea v-model="createForm.notes" :rows="2" class="w-full" />
                </UFormField>
              </div>
              <UAlert v-if="createError" color="error" variant="soft" :description="createError" />
            </div>

            <!-- Footer -->
            <div class="flex shrink-0 items-center justify-end gap-3 border-t border-gray-100 px-6 py-4">
              <UButton variant="ghost" color="neutral" @click="showCreateModal = false">Cancel</UButton>
              <UButton :loading="savingCreate" leading-icon="i-heroicons-check" @click="submitCreate">Create Work Order</UButton>
            </div>
          </div>
        </template>
    </UModal>

    <!-- List -->
    <UCard :ui="{ root: 'flex flex-col flex-1 min-h-0', body: 'flex flex-col flex-1 min-h-0 p-0' }">
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <div class="flex flex-wrap items-center gap-3">
            <UInput v-model="search" placeholder="Search by WO #, asset or description..." leading-icon="i-heroicons-magnifying-glass" class="max-w-xs" />
            <USelect v-model="statusFilter" :items="statusOptions" class="w-48" />
            <USelect v-model="priorityFilter" :items="filterPriorityOptions" class="w-40" />
          </div>
          <UButton leading-icon="i-heroicons-plus" @click="openCreate" class="!bg-blue-700 hover:!bg-blue-800">New Work Order</UButton>
        </div>
      </template>

      <!-- Tabs -->
      <UTabs v-model="activeTab" :items="tabs" :ui="{ root: 'flex flex-col flex-1 min-h-0 w-full', list: 'border-b border-gray-100 px-5 pt-1 rounded-none bg-white shrink-0', content: 'flex-1 min-h-0' }">
        <template #todo>
          <div class="overflow-auto h-full p-4 space-y-2">
            <div v-if="filteredTodo.length === 0" class="py-12 text-center text-sm text-gray-400">
              No open work orders found.
            </div>
            <template v-else>
              <div
                v-for="wo in filteredTodo"
                :key="wo.work_order_id"
                class="flex cursor-pointer items-start gap-4 rounded-lg px-5 py-4 ring-1 ring-gray-200 hover:bg-blue-50/40 transition-colors border-l-4"
                :class="isOverdue(wo) ? 'border-l-blue-500' : 'border-l-transparent'"
                @click="openEdit(wo)"
              >
                <!-- Left icon -->
                <div class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gray-100">
                  <UIcon name="i-heroicons-clipboard-document-list" class="h-4 w-4 text-gray-400" />
                </div>

                <!-- Main content -->
                <div class="min-w-0 flex-1">
                  <!-- Title -->
                  <div class="flex items-center gap-1.5">
                    <UIcon v-if="wo.asset_pm_id" name="i-heroicons-arrow-path" class="h-3.5 w-3.5 shrink-0 text-gray-400" />
                    <span class="text-sm font-semibold text-slate-800 truncate">
                      {{ wo.description ? (wo.description.length > 60 ? wo.description.slice(0, 60) + '…' : wo.description) : `Work Order #${wo.work_order_id}` }}
                    </span>
                    <span class="h-2 w-2 shrink-0 rounded-full bg-blue-500" />
                  </div>
                  <!-- Asset -->
                  <p class="mt-0.5 text-xs text-gray-500">Asset: {{ wo.asset_id ?? '—' }}</p>
                  <!-- Meta row: type · supplier · issue date -->
                  <div class="mt-1.5 flex flex-wrap items-center gap-2">
                    <span
                      v-if="wo.typ"
                      class="inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium capitalize"
                      :class="typeStyles[wo.typ] ?? 'bg-gray-100 text-gray-500'"
                    >{{ wo.typ }}</span>
                    <span v-if="wo.supplier_id && supplierMap[wo.supplier_id]" class="flex items-center gap-1 text-[11px] text-gray-500">
                      <UIcon name="i-heroicons-building-storefront" class="h-3 w-3" />
                      {{ supplierMap[wo.supplier_id] }}
                    </span>
                    <span v-if="wo.issue_date" class="flex items-center gap-1 text-[11px] text-gray-400">
                      <UIcon name="i-heroicons-calendar" class="h-3 w-3" />
                      Issued {{ formatDate(wo.issue_date) }}
                    </span>
                  </div>
                  <!-- Status dropdown + actions -->
                  <div class="mt-2 flex items-center gap-2">
                    <UDropdownMenu
                      :items="woStatusOptions.map(s => ({ label: s.replace(/_/g, ' '), onSelect: () => quickStatusChange(wo, s) }))"
                      @click.stop
                    >
                      <span
                        class="inline-flex cursor-pointer items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium capitalize transition-opacity hover:opacity-80"
                        :class="statusStyles[wo.status] ?? 'bg-gray-100 text-gray-500'"
                      >
                        <UIcon name="i-heroicons-arrow-path" class="h-3 w-3" />
                        {{ wo.status.replace(/_/g, ' ') }}
                        <UIcon name="i-heroicons-chevron-down" class="h-3 w-3" />
                      </span>
                    </UDropdownMenu>
                    <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click.stop="deleteTarget = wo" />
                  </div>
                </div>

                <!-- Right side -->
                <div class="shrink-0 flex flex-col items-end gap-1">
                  <div class="flex h-8 w-8 items-center justify-center rounded-full bg-blue-900">
                    <UIcon name="i-heroicons-user-group" class="h-4 w-4 text-blue-200" />
                  </div>
                  <span class="text-xs text-gray-500">#{{ wo.work_order_id }}</span>
                  <div class="flex flex-col items-end gap-0.5 mt-0.5">
                    <span v-if="isOverdue(wo)" class="flex items-center gap-1 text-[11px] text-orange-500 font-medium">
                      <UIcon name="i-heroicons-clock" class="h-3.5 w-3.5" />
                      Overdue
                    </span>
                    <span class="flex items-center gap-1.5 text-[11px] text-gray-600 font-medium">
                      <span
                        class="h-2 w-2 rounded-full shrink-0"
                        :class="wo.priority === 'High' ? 'bg-red-500' : wo.priority === 'Medium' ? 'bg-yellow-400' : 'bg-gray-300'"
                      />
                      {{ wo.priority }}
                    </span>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </template>

        <template #done>
          <div class="overflow-auto h-full p-4 space-y-2">
            <div v-if="filteredDone.length === 0" class="py-12 text-center text-sm text-gray-400">
              No completed work orders found.
            </div>
            <template v-else>
              <div
                v-for="wo in filteredDone"
                :key="wo.work_order_id"
                class="flex cursor-pointer items-start gap-4 rounded-lg border-l-4 border-l-transparent px-5 py-4 ring-1 ring-gray-200 hover:bg-slate-50/60 transition-colors"
                @click="openEdit(wo)"
              >
                <!-- Left icon -->
                <div class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gray-100">
                  <UIcon name="i-heroicons-check-circle" class="h-4 w-4 text-gray-400" />
                </div>

                <!-- Main content -->
                <div class="min-w-0 flex-1">
                  <!-- Title -->
                  <div class="flex items-center gap-1.5">
                    <UIcon v-if="wo.asset_pm_id" name="i-heroicons-arrow-path" class="h-3.5 w-3.5 shrink-0 text-gray-300" />
                    <span class="text-sm font-semibold text-slate-500 truncate">
                      {{ wo.description ? (wo.description.length > 60 ? wo.description.slice(0, 60) + '…' : wo.description) : `Work Order #${wo.work_order_id}` }}
                    </span>
                  </div>
                  <!-- Asset -->
                  <p class="mt-0.5 text-xs text-gray-400">Asset: {{ wo.asset_id ?? '—' }}</p>
                  <!-- Meta row -->
                  <div class="mt-1.5 flex flex-wrap items-center gap-2">
                    <span
                      v-if="wo.typ"
                      class="inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium capitalize opacity-60"
                      :class="typeStyles[wo.typ] ?? 'bg-gray-100 text-gray-500'"
                    >{{ wo.typ }}</span>
                    <span v-if="wo.supplier_id && supplierMap[wo.supplier_id]" class="flex items-center gap-1 text-[11px] text-gray-400">
                      <UIcon name="i-heroicons-building-storefront" class="h-3 w-3" />
                      {{ supplierMap[wo.supplier_id] }}
                    </span>
                    <span v-if="wo.date_completed" class="flex items-center gap-1 text-[11px] text-gray-400">
                      <UIcon name="i-heroicons-check" class="h-3 w-3" />
                      Completed {{ formatDate(wo.date_completed) }}
                    </span>
                    <span v-else-if="wo.issue_date" class="flex items-center gap-1 text-[11px] text-gray-400">
                      <UIcon name="i-heroicons-calendar" class="h-3 w-3" />
                      Issued {{ formatDate(wo.issue_date) }}
                    </span>
                  </div>
                  <!-- Status + actions -->
                  <div class="mt-2 flex items-center gap-2">
                    <span
                      class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium capitalize"
                      :class="statusStyles[wo.status] ?? 'bg-gray-100 text-gray-500'"
                    >{{ wo.status.replace(/_/g, ' ') }}</span>
                    <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click.stop="deleteTarget = wo" />
                  </div>
                </div>

                <!-- Right side -->
                <div class="shrink-0 flex flex-col items-end gap-1">
                  <div class="flex h-8 w-8 items-center justify-center rounded-full bg-slate-200">
                    <UIcon name="i-heroicons-user-group" class="h-4 w-4 text-slate-400" />
                  </div>
                  <span class="text-xs text-gray-400">#{{ wo.work_order_id }}</span>
                  <span class="flex items-center gap-1.5 text-[11px] text-gray-400 font-medium mt-0.5">
                    <span
                      class="h-2 w-2 rounded-full shrink-0 opacity-60"
                      :class="wo.priority === 'High' ? 'bg-red-500' : wo.priority === 'Medium' ? 'bg-yellow-400' : 'bg-gray-300'"
                    />
                    {{ wo.priority }}
                  </span>
                </div>
              </div>
            </template>
          </div>
        </template>
      </UTabs>
    </UCard>

    <!-- Edit Modal -->
    <WorkOrderModal v-model:open="showEditModal" :work-order-id="editingId" @saved="refresh" />

    <!-- Delete modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Work Order</h3></template>
          <p class="text-sm text-gray-600">
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
