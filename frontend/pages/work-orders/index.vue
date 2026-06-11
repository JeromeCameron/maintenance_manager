<script setup lang="ts">
import type { WorkOrder, WorkOrderPart, AssetPM } from "~/types"

const { getAll, getOne, create, update, remove, getPartsByWorkOrder, addPart, updatePart, removePart } = useWorkOrders()
const { getAll: getAssets } = useAssets()
const { getAll: getSuppliers } = useSuppliers()
const { getPMsByAsset } = useMaintenance()

const { data: workOrders, refresh } = await useAsyncData("work-orders", () => getAll())
const [{ data: assets }, { data: suppliers }] = await Promise.all([
  useAsyncData("assets-select", () => getAssets()),
  useAsyncData("suppliers-select", () => getSuppliers()),
])

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

const filtered = computed(() =>
  (workOrders.value ?? []).filter((w) => {
    const matchSearch =
      !search.value ||
      String(w.work_order_id).includes(search.value) ||
      (w.asset_id ?? "").toLowerCase().includes(search.value.toLowerCase())
    const matchStatus = !statusFilter.value || w.status === statusFilter.value
    const matchPriority = !priorityFilter.value || w.priority === priorityFilter.value
    return matchSearch && matchStatus && matchPriority
  })
)

const priorityOptions = ["Low", "Medium", "High"]
const typeOptions = ["corrective", "predictive", "preventative", "inspection", "project"]
const woStatusOptions = ["requested", "scheduled", "awaiting_parts", "awaiting_po", "in_progress", "on_hold", "cancelled", "completed", "closed"]

const assetOptions = computed(() =>
  (assets.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id }))
)
const supplierOptions = computed(() =>
  [{ label: "None", value: undefined }, ...(suppliers.value ?? []).map((s) => ({ label: s.name, value: s.supplier_id }))]
)

// ── Shared PM logic ───────────────────────────────────────────
const createAssetPMs = ref<AssetPM[]>([])
const editAssetPMs = ref<AssetPM[]>([])

async function loadPMsForAsset(assetId: string | undefined, target: "create" | "edit") {
  const list = assetId ? (await getPMsByAsset(assetId) ?? []) : []
  if (target === "create") createAssetPMs.value = list
  else editAssetPMs.value = list
}

const createPMOptions = computed(() =>
  [{ label: "None", value: undefined }, ...createAssetPMs.value.map((p) => ({ label: `${p.pm_plan_id} — next: ${p.next_service ?? "—"}`, value: p.id }))]
)
const editPMOptions = computed(() =>
  [{ label: "None", value: undefined }, ...editAssetPMs.value.map((p) => ({ label: `${p.pm_plan_id} — next: ${p.next_service ?? "—"}`, value: p.id }))]
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
  loadPMsForAsset(id, "create")
})

function onCreateOpen(isOpen: boolean) {
  if (isOpen) {
    createForm.value = defaultForm()
    createError.value = null
    createAssetPMs.value = []
  }
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
const editForm = ref<Partial<WorkOrder>>({})
const editingId = ref<number | null>(null)
const savingEdit = ref(false)
const editError = ref<string | null>(null)
const loadingEdit = ref(false)

watch(() => editForm.value.asset_id, (id) => {
  editForm.value.asset_pm_id = undefined
  loadPMsForAsset(id, "edit")
})

async function openEdit(wo: WorkOrder) {
  loadingEdit.value = true
  showEditModal.value = true
  editingId.value = wo.work_order_id!
  const full = await getOne(wo.work_order_id!)
  editForm.value = { ...full }
  if (full?.asset_id) await loadPMsForAsset(full.asset_id, "edit")
  parts.value = await getPartsByWorkOrder(wo.work_order_id!) ?? []
  loadingEdit.value = false
}

async function submitEdit() {
  savingEdit.value = true
  editError.value = null
  try {
    await update(editingId.value!, editForm.value as WorkOrder)
    await refresh()
    showEditModal.value = false
  } catch (e: unknown) {
    editError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingEdit.value = false
  }
}

// ── Parts (edit modal) ────────────────────────────────────────
const parts = ref<WorkOrderPart[]>([])
const newPart = ref<Partial<WorkOrderPart>>({ quantity_used: 1 })
const addingPart = ref(false)
const editingPart = ref<WorkOrderPart | null>(null)
const editPartDraft = ref<Partial<WorkOrderPart>>({})
const savingPart = ref(false)

const partColumns = [
  { accessorKey: "part_no", header: "Part No" },
  { accessorKey: "quantity_used", header: "Qty" },
  { accessorKey: "unit_cost", header: "Unit Cost" },
  { accessorKey: "total_cost", header: "Total" },
  { id: "part-actions", header: "" },
]

async function submitPart() {
  if (!editingId.value || !newPart.value.part_no) return
  addingPart.value = true
  try {
    const created = await addPart({ ...newPart.value, work_order_id: editingId.value } as WorkOrderPart)
    parts.value = [...parts.value, created]
    newPart.value = { quantity_used: 1 }
  } finally {
    addingPart.value = false
  }
}

function startEditPart(part: WorkOrderPart) {
  editingPart.value = part
  editPartDraft.value = { ...part }
}
function cancelEditPart() { editingPart.value = null; editPartDraft.value = {} }

async function saveEditPart() {
  if (!editingPart.value?.id) return
  savingPart.value = true
  try {
    const updated = await updatePart(editingPart.value.id, editPartDraft.value as WorkOrderPart)
    parts.value = parts.value.map((p) => p.id === updated.id ? updated : p)
    cancelEditPart()
  } finally {
    savingPart.value = false
  }
}

async function deletePart(id: number) {
  await removePart(id)
  parts.value = parts.value.filter((p) => p.id !== id)
  if (editingPart.value?.id === id) cancelEditPart()
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
      <UModal v-model:open="showCreateModal" :ui="{ content: 'max-w-2xl' }" @update:open="onCreateOpen">
        <UButton leading-icon="i-heroicons-plus">New Work Order</UButton>
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
    </div>

    <!-- List -->
    <UCard>
      <template #header>
        <div class="flex flex-wrap items-center gap-3">
          <UInput v-model="search" placeholder="Search by WO # or asset..." leading-icon="i-heroicons-magnifying-glass" class="max-w-xs" />
          <USelect v-model="statusFilter" :items="statusOptions" class="w-48" />
          <USelect v-model="priorityFilter" :items="filterPriorityOptions" class="w-40" />
        </div>
      </template>

      <UTable :data="filtered" :columns="columns">
        <template #status-cell="{ row: { original: row } }">
          <UBadge :color="statusColors[row.status] ?? 'neutral'" variant="soft">{{ row.status.replace(/_/g, " ") }}</UBadge>
        </template>
        <template #priority-cell="{ row: { original: row } }">
          <UBadge :color="row.priority === 'High' ? 'error' : row.priority === 'Medium' ? 'warning' : 'neutral'" variant="soft">{{ row.priority }}</UBadge>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEdit(row)" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Edit Modal -->
    <UModal v-model:open="showEditModal" :ui="{ content: 'max-w-3xl' }">
      <template #content>
        <div class="flex max-h-[90vh] w-full max-w-3xl flex-col rounded-xl bg-white shadow-xl">
          <!-- Header -->
          <div class="flex shrink-0 items-center justify-between border-b border-gray-100 px-6 py-5">
            <h3 class="text-base font-semibold text-slate-900">Edit Work Order #{{ editingId }}</h3>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showEditModal = false" />
          </div>

          <div v-if="loadingEdit" class="flex flex-1 items-center justify-center py-16">
            <UIcon name="i-heroicons-arrow-path" class="h-6 w-6 animate-spin text-gray-400" />
          </div>

          <!-- Scrollable body -->
          <div v-else class="flex-1 overflow-y-auto px-6 py-5 space-y-6">
            <!-- Details section -->
            <div class="grid grid-cols-2 gap-x-5 gap-y-4">
              <UFormField label="Asset" class="col-span-2">
                <USelect v-model="editForm.asset_id" :items="assetOptions" placeholder="Select asset…" class="w-full" />
              </UFormField>
              <UFormField label="Supplier">
                <USelect v-model="editForm.supplier_id" :items="supplierOptions" placeholder="Select supplier…" class="w-full" />
              </UFormField>
              <UFormField label="PM Plan">
                <USelect v-model="editForm.asset_pm_id" :items="editPMOptions" placeholder="Link to PM (optional)" class="w-full" />
              </UFormField>
              <UFormField label="Priority">
                <USelect v-model="editForm.priority" :items="priorityOptions" class="w-full" />
              </UFormField>
              <UFormField label="Type">
                <USelect v-model="editForm.typ" :items="typeOptions" class="w-full" />
              </UFormField>
              <UFormField label="Status">
                <USelect v-model="editForm.status" :items="woStatusOptions" class="w-full" />
              </UFormField>
              <UFormField label="Issue Date">
                <UInput v-model="editForm.issue_date" type="date" class="w-full" />
              </UFormField>
              <UFormField label="Expected Date">
                <UInput v-model="editForm.expected_date" type="date" class="w-full" />
              </UFormField>
              <UFormField label="Date Completed">
                <UInput v-model="editForm.date_completed" type="date" class="w-full" />
              </UFormField>
              <UFormField label="Estimated Hours">
                <UInput v-model.number="editForm.estimated_hours" type="number" step="0.5" class="w-full" />
              </UFormField>
              <UFormField label="Actual Hours">
                <UInput v-model.number="editForm.actual_hours" type="number" step="0.5" class="w-full" />
              </UFormField>
              <UFormField label="Estimated Cost ($)">
                <UInput v-model.number="editForm.estimated_cost" type="number" step="0.01" class="w-full" />
              </UFormField>
              <UFormField label="Actual Cost ($)">
                <UInput v-model.number="editForm.actual_cost" type="number" step="0.01" class="w-full" />
              </UFormField>
              <UFormField label="Description" class="col-span-2">
                <UTextarea v-model="editForm.description" :rows="3" class="w-full" />
              </UFormField>
              <UFormField label="Notes" class="col-span-2">
                <UTextarea v-model="editForm.notes" :rows="2" class="w-full" />
              </UFormField>
            </div>

            <!-- Parts section -->
            <div>
              <div class="mb-3 flex items-center gap-3">
                <span class="text-xs font-semibold uppercase tracking-wider text-gray-400">Parts Used</span>
                <div class="flex-1 border-t border-gray-100" />
              </div>

              <UTable :data="parts" :columns="partColumns">
                <template #part-actions-cell="{ row: { original: row } }">
                  <div class="flex items-center gap-1">
                    <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="startEditPart(row)" />
                    <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deletePart(row.id)" />
                  </div>
                </template>
              </UTable>

              <!-- Edit part form -->
              <div v-if="editingPart" class="mt-3 grid grid-cols-4 gap-3 rounded-lg border border-primary-200 bg-primary-50 p-3">
                <UFormField label="Part No">
                  <UInput v-model="editPartDraft.part_no" class="w-full" />
                </UFormField>
                <UFormField label="Qty">
                  <UInput v-model.number="editPartDraft.quantity_used" type="number" min="1" class="w-full" />
                </UFormField>
                <UFormField label="Unit Cost">
                  <UInput v-model.number="editPartDraft.unit_cost" type="number" step="0.01" class="w-full" />
                </UFormField>
                <div class="flex items-end gap-2">
                  <UButton size="sm" :loading="savingPart" @click="saveEditPart">Update</UButton>
                  <UButton size="sm" variant="ghost" color="neutral" @click="cancelEditPart">Cancel</UButton>
                </div>
              </div>

              <!-- Add part form -->
              <div v-else class="mt-3 grid grid-cols-4 gap-3 border-t pt-3">
                <UFormField label="Part No">
                  <UInput v-model="newPart.part_no" placeholder="e.g. BLT-001" class="w-full" />
                </UFormField>
                <UFormField label="Qty">
                  <UInput v-model.number="newPart.quantity_used" type="number" min="1" class="w-full" />
                </UFormField>
                <UFormField label="Unit Cost">
                  <UInput v-model.number="newPart.unit_cost" type="number" step="0.01" class="w-full" />
                </UFormField>
                <div class="flex items-end">
                  <UButton size="sm" :loading="addingPart" @click="submitPart">Add Part</UButton>
                </div>
              </div>
            </div>

            <UAlert v-if="editError" color="error" variant="soft" :description="editError" />
          </div>

          <!-- Footer -->
          <div class="flex shrink-0 items-center justify-end gap-3 border-t border-gray-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showEditModal = false">Cancel</UButton>
            <UButton :loading="savingEdit" @click="submitEdit">Save Changes</UButton>
          </div>
        </div>
      </template>
    </UModal>

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
