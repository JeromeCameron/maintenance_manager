<script setup lang="ts">
import type { WorkOrder, WorkOrderPart, AssetPM } from "~/types"

const props = defineProps<{ workOrderId: number | null }>()
const open = defineModel<boolean>("open", { default: false })
const emit = defineEmits<{ saved: [] }>()

const { isAdmin } = useAuth()
const { getOne, update, getPartsByWorkOrder, addPart, updatePart, removePart } = useWorkOrders()
const { getAll: getAssets } = useAssets()
const { getAll: getSuppliers } = useSuppliers()
const { getPMsByAsset } = useMaintenance()
const { getParts, getStockLevels } = useInventory()
const { getAll: getLocations } = useLocations()

const [{ data: assets }, { data: suppliers }, { data: inventoryParts }, { data: locations }, { data: stockLevels }] = await Promise.all([
  useAsyncData("wo-modal-assets", () => getAssets()),
  useAsyncData("wo-modal-suppliers", () => getSuppliers()),
  useAsyncData("wo-modal-parts", () => getParts()),
  useAsyncData("wo-modal-locations", () => getLocations()),
  useAsyncData("wo-modal-stock-levels", () => getStockLevels()),
])

const woStatusColors: Record<string, string> = {
  requested: "info", scheduled: "info", in_progress: "warning", awaiting_parts: "warning",
  awaiting_po: "warning", on_hold: "neutral", cancelled: "error", completed: "success", closed: "neutral",
}
const priorityColors: Record<string, string> = {
  High: "error", Medium: "warning", Low: "neutral",
}

const priorityOptions = ["Low", "Medium", "High"]
const typeOptions = ["corrective", "predictive", "preventative", "inspection", "project"]
const woStatusOptions = ["requested", "scheduled", "awaiting_parts", "awaiting_po", "in_progress", "on_hold", "cancelled", "completed", "closed"]
const plannedOptions = [
  { label: "Planned", value: true },
  { label: "Unplanned", value: false },
]

const assetOptions = computed(() =>
  (assets.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id }))
)
const supplierOptions = computed(() =>
  [{ label: "None", value: undefined }, ...(suppliers.value ?? []).map((s) => ({ label: s.name, value: s.supplier_id }))]
)
const partOptions = computed(() =>
  (inventoryParts.value ?? []).map((p) => ({ label: `${p.part_no} — ${p.part_name}`, value: p.part_no }))
)
const locationOptions = computed(() =>
  (locations.value ?? []).map((l) => ({ label: l.name, value: l.location_id }))
)
const locationMap = computed(() => {
  const m: Record<number, string> = {}
  for (const l of locations.value ?? []) if (l.location_id != null) m[l.location_id] = l.name
  return m
})
// The asset's home depot, used as the default location to pull stock from.
const defaultLocationId = computed(() =>
  (assets.value ?? []).find((a) => a.asset_id === form.value.asset_id)?.location_id
)
function stockAvailable(partNo: string | undefined, locationId: number | undefined): number | null {
  if (!partNo) return null
  const sl = (stockLevels.value ?? []).find((s) => s.part_no === partNo && (locationId == null ? s.location_id == null : s.location_id === locationId))
  return sl?.quantity ?? 0
}

// ── Form state ────────────────────────────────────────────────
const form = ref<Partial<WorkOrder>>({})
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)

// ── PM options ────────────────────────────────────────────────
const assetPMs = ref<AssetPM[]>([])
const pmOptions = computed(() =>
  [{ label: "None", value: undefined }, ...assetPMs.value.map((p) => ({ label: `${p.pm_plan_id} — next: ${p.next_service ?? "—"}`, value: p.id }))]
)

watch(() => form.value.asset_id, async (id, oldId) => {
  if (oldId !== undefined) form.value.asset_pm_id = undefined
  assetPMs.value = id ? (await getPMsByAsset(id) ?? []) : []
})

// ── Parts ─────────────────────────────────────────────────────
// Adding a part here also auto-issues a matching stock transaction (backend-side),
// so stock no longer needs a separate manual entry on the Inventory page.
const parts = ref<WorkOrderPart[]>([])
const newPart = ref<Partial<WorkOrderPart>>({ quantity_used: 1, location_id: defaultLocationId.value })
const addingPart = ref(false)
const editingPart = ref<WorkOrderPart | null>(null)
const editPartDraft = ref<Partial<WorkOrderPart>>({})
const savingPart = ref(false)

const partColumns = [
  { accessorKey: "part_no", header: "Part No" },
  { accessorKey: "quantity_used", header: "Qty" },
  { accessorKey: "unit_cost", header: "Unit Cost" },
  { accessorKey: "total_cost", header: "Total" },
  { accessorKey: "location_id", header: "Issued From" },
  { id: "part-actions", header: "" },
]

async function submitPart() {
  if (!props.workOrderId || !newPart.value.part_no) return
  addingPart.value = true
  try {
    const created = await addPart({ ...newPart.value, work_order_id: props.workOrderId } as WorkOrderPart)
    parts.value = [...parts.value, created]
    newPart.value = { quantity_used: 1, location_id: defaultLocationId.value }
  } finally { addingPart.value = false }
}

function startEditPart(part: WorkOrderPart) { editingPart.value = part; editPartDraft.value = { ...part } }
function cancelEditPart() { editingPart.value = null; editPartDraft.value = {} }

async function saveEditPart() {
  if (!editingPart.value?.id) return
  savingPart.value = true
  try {
    const updated = await updatePart(editingPart.value.id, editPartDraft.value as WorkOrderPart)
    parts.value = parts.value.map((p) => p.id === updated.id ? updated : p)
    cancelEditPart()
  } finally { savingPart.value = false }
}

async function deletePart(id: number) {
  await removePart(id)
  parts.value = parts.value.filter((p) => p.id !== id)
  if (editingPart.value?.id === id) cancelEditPart()
}

// ── Modal tab ─────────────────────────────────────────────────
const modalTab = ref<'details' | 'parts' | 'notes'>('details')

// ── Load when opened ──────────────────────────────────────────
// Guards against a stale response: if the modal is closed or switched to a
// different work order before this fetch resolves, its result is discarded
// instead of overwriting the form with the wrong work order's data.
watch([open, () => props.workOrderId], async ([isOpen, id]) => {
  if (!isOpen || !id) {
    if (!isOpen) { form.value = {}; parts.value = []; error.value = null; loading.value = false }
    return
  }
  loading.value = true
  error.value = null
  modalTab.value = 'details'
  const isStale = () => !open.value || props.workOrderId !== id
  try {
    const full = await getOne(id as number)
    if (isStale()) return
    form.value = { ...full }
    const [pms, woParts] = await Promise.all([
      full?.asset_id ? getPMsByAsset(full.asset_id) : Promise.resolve([]),
      getPartsByWorkOrder(id as number),
    ])
    if (isStale()) return
    assetPMs.value = pms ?? []
    parts.value = woParts ?? []
    newPart.value = { quantity_used: 1, location_id: defaultLocationId.value }
  } catch (e: unknown) {
    if (isStale()) return
    error.value = (e as { message?: string }).message ?? "Failed to load work order"
  } finally {
    if (!isStale()) loading.value = false
  }
})

// ── Save ──────────────────────────────────────────────────────
async function save() {
  if (!props.workOrderId) return
  saving.value = true
  error.value = null
  try {
    await update(props.workOrderId, form.value as WorkOrder)
    emit("saved")
    open.value = false
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message ?? "Save failed"
  } finally { saving.value = false }
}
</script>

<template>
  <UModal v-model:open="open" :ui="{ content: 'max-w-3xl' }">
    <template #content>
      <div class="flex max-h-[90vh] w-full max-w-3xl flex-col rounded-xl bg-white shadow-xl dark:bg-slate-900">
        <!-- Header -->
        <div class="flex shrink-0 items-start justify-between border-b border-gray-100 dark:border-slate-800 px-6 py-5">
          <div>
            <div class="flex items-center gap-2">
              <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">Work Order #{{ workOrderId }}</h3>
              <UBadge v-if="form.status" :color="woStatusColors[form.status] ?? 'neutral'" variant="soft" size="sm">
                {{ form.status.replace(/_/g, ' ') }}
              </UBadge>
              <UBadge v-if="form.priority" :color="priorityColors[form.priority] ?? 'neutral'" variant="soft" size="sm">
                {{ form.priority }}
              </UBadge>
            </div>
            <p v-if="form.asset_id" class="mt-1 text-xs text-slate-400 dark:text-slate-500">{{ form.asset_id }}</p>
          </div>
          <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="open = false" />
        </div>

        <div v-if="loading" class="flex flex-1 items-center justify-center py-16">
          <UIcon name="i-heroicons-arrow-path" class="h-6 w-6 animate-spin text-gray-400 dark:text-slate-500" />
        </div>

        <template v-else>
          <!-- Tab bar -->
          <div class="flex shrink-0 gap-1 border-b border-gray-100 dark:border-slate-800 px-6">
            <button
              v-for="tab in [
                { key: 'details', label: 'Details' },
                { key: 'parts',   label: `Parts${parts.length ? ` (${parts.length})` : ''}` },
                { key: 'notes',   label: 'Notes' },
              ]"
              :key="tab.key"
              class="border-b-2 px-3 py-3 text-sm font-medium transition-colors"
              :class="modalTab === tab.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-100'"
              @click="modalTab = tab.key as typeof modalTab"
            >{{ tab.label }}</button>
          </div>

          <!-- Details tab -->
          <div v-if="modalTab === 'details'" class="flex-1 overflow-y-auto px-6 py-5">
            <div class="grid grid-cols-2 gap-x-5 gap-y-5">
              <div>
                <label class="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-300">Asset</label>
                <USelect v-model="form.asset_id" :items="assetOptions" placeholder="Select asset…" class="w-full" size="lg" :ui="{ base: 'bg-slate-50 dark:bg-slate-800' }" />
              </div>
              <div>
                <label class="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-300">Supplier</label>
                <USelect v-model="form.supplier_id" :items="supplierOptions" placeholder="Select supplier…" class="w-full" size="lg" :ui="{ base: 'bg-slate-50 dark:bg-slate-800' }" />
              </div>
              <div>
                <label class="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-300">PM Plan</label>
                <USelect v-model="form.asset_pm_id" :items="pmOptions" placeholder="Link to PM (optional)" class="w-full" size="lg" :ui="{ base: 'bg-slate-50 dark:bg-slate-800' }" />
              </div>
              <div>
                <label class="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-300">Type</label>
                <USelect v-model="form.typ" :items="typeOptions" class="w-full" size="lg" :ui="{ base: 'bg-slate-50 dark:bg-slate-800' }" />
              </div>
              <div>
                <label class="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-300">Priority</label>
                <USelect v-model="form.priority" :items="priorityOptions" class="w-full" size="lg" :ui="{ base: 'bg-slate-50 dark:bg-slate-800' }" />
              </div>
              <div>
                <label class="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-300">Planned / Unplanned</label>
                <USelect v-model="form.planned" :items="plannedOptions" placeholder="Select…" class="w-full" size="lg" :ui="{ base: 'bg-slate-50 dark:bg-slate-800' }" />
              </div>
              <div>
                <label class="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-300">Status</label>
                <USelect v-model="form.status" :items="woStatusOptions" class="w-full" size="lg" :ui="{ base: 'bg-slate-50 dark:bg-slate-800' }" />
              </div>
              <div>
                <label class="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-300">Issue Date</label>
                <UInput v-model="form.issue_date" type="date" class="w-full" size="lg" :ui="{ base: 'bg-slate-50 dark:bg-slate-800' }" />
              </div>
              <div>
                <label class="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-300">Expected Date</label>
                <UInput v-model="form.expected_date" type="date" class="w-full" size="lg" :ui="{ base: 'bg-slate-50 dark:bg-slate-800' }" />
              </div>
              <div>
                <label class="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-300">Date Completed</label>
                <UInput v-model="form.date_completed" type="date" class="w-full" size="lg" :ui="{ base: 'bg-slate-50 dark:bg-slate-800' }" />
              </div>
              <div>
                <label class="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-300">Estimated Hours</label>
                <UInput v-model.number="form.estimated_hours" type="number" step="0.5" class="w-full" size="lg" :ui="{ base: 'bg-slate-50 dark:bg-slate-800' }" />
              </div>
              <div>
                <label class="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-300">Actual Hours</label>
                <UInput v-model.number="form.actual_hours" type="number" step="0.5" class="w-full" size="lg" :ui="{ base: 'bg-slate-50 dark:bg-slate-800' }" />
              </div>
              <div>
                <label class="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-300">Estimated Cost ($)</label>
                <UInput v-model.number="form.estimated_cost" type="number" step="0.01" class="w-full" size="lg" :ui="{ base: 'bg-slate-50 dark:bg-slate-800' }" />
              </div>
              <div>
                <label class="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-300">Actual Cost ($)</label>
                <UInput v-model.number="form.actual_cost" type="number" step="0.01" class="w-full" size="lg" :ui="{ base: 'bg-slate-50 dark:bg-slate-800' }" />
              </div>
              <div class="col-span-2">
                <label class="mb-1.5 block text-sm font-semibold text-slate-700 dark:text-slate-300">Description</label>
                <UTextarea v-model="form.description" :rows="4" class="w-full" placeholder="Describe the work to be done…" :ui="{ base: 'bg-slate-50 dark:bg-slate-800' }" />
              </div>
            </div>
            <UAlert v-if="error" color="error" variant="soft" :description="error" class="mt-5" />
          </div>

          <!-- Parts tab -->
          <div v-else-if="modalTab === 'parts'" class="flex-1 overflow-y-auto px-6 py-5 space-y-4">
            <UTable :data="parts" :columns="partColumns">
              <template #location_id-cell="{ row: { original: row } }">
                {{ row.location_id != null ? (locationMap[row.location_id] ?? row.location_id) : "—" }}
              </template>
              <template #part-actions-cell="{ row: { original: row } }">
                <div class="flex items-center gap-1">
                  <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="startEditPart(row)" />
                  <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deletePart(row.id)" />
                </div>
              </template>
            </UTable>
            <p class="text-xs text-slate-400 dark:text-slate-500">
              Adding or editing a part here automatically issues a matching stock transaction — no need to record it separately on the Inventory page.
            </p>

            <div v-if="editingPart" class="grid grid-cols-6 gap-3 rounded-lg border border-primary-200 dark:border-primary-500/20 bg-primary-50 dark:bg-primary-500/10 p-3">
              <UFormField label="Part No" class="col-span-2">
                <USelect v-model="editPartDraft.part_no" :items="partOptions" placeholder="Select part…" class="w-full" />
              </UFormField>
              <UFormField label="Qty">
                <UInput v-model.number="editPartDraft.quantity_used" type="number" min="1" class="w-full" />
              </UFormField>
              <UFormField label="Unit Cost">
                <UInput v-model.number="editPartDraft.unit_cost" type="number" step="0.01" class="w-full" />
              </UFormField>
              <UFormField label="Issue From">
                <USelect v-model="editPartDraft.location_id" :items="locationOptions" placeholder="Location…" class="w-full" />
                <p v-if="editPartDraft.part_no" class="mt-1 text-xs text-slate-400 dark:text-slate-500">
                  {{ stockAvailable(editPartDraft.part_no, editPartDraft.location_id) }} in stock
                </p>
              </UFormField>
              <div class="flex items-end gap-2">
                <UButton size="sm" :loading="savingPart" @click="saveEditPart">Update</UButton>
                <UButton size="sm" variant="ghost" color="neutral" @click="cancelEditPart">Cancel</UButton>
              </div>
            </div>

            <div v-else class="grid grid-cols-6 gap-3 rounded-lg border border-gray-100 dark:border-slate-800 bg-gray-50 dark:bg-slate-800 p-3">
              <UFormField label="Part No" class="col-span-2">
                <USelect v-model="newPart.part_no" :items="partOptions" placeholder="Select part…" class="w-full" />
              </UFormField>
              <UFormField label="Qty">
                <UInput v-model.number="newPart.quantity_used" type="number" min="1" class="w-full" />
              </UFormField>
              <UFormField label="Unit Cost">
                <UInput v-model.number="newPart.unit_cost" type="number" step="0.01" class="w-full" />
              </UFormField>
              <UFormField label="Issue From">
                <USelect v-model="newPart.location_id" :items="locationOptions" placeholder="Location…" class="w-full" />
                <p v-if="newPart.part_no" class="mt-1 text-xs text-slate-400 dark:text-slate-500">
                  {{ stockAvailable(newPart.part_no, newPart.location_id) }} in stock
                </p>
              </UFormField>
              <div class="flex items-end">
                <UButton size="sm" :loading="addingPart" @click="submitPart">Add Part</UButton>
              </div>
            </div>
          </div>

          <!-- Notes tab -->
          <div v-else-if="modalTab === 'notes'" class="flex-1 overflow-y-auto px-6 py-5">
            <UFormField label="Notes">
              <UTextarea v-model="form.notes" :rows="12" class="w-full" placeholder="Add notes here…" />
            </UFormField>
            <UAlert v-if="error" color="error" variant="soft" :description="error" class="mt-4" />
          </div>

          <!-- Footer -->
          <div class="flex shrink-0 items-center justify-end gap-3 border-t border-gray-100 dark:border-slate-800 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="open = false">Cancel</UButton>
            <UButton v-if="modalTab !== 'parts'" :loading="saving" @click="save">Save Changes</UButton>
          </div>
        </template>
      </div>
    </template>
  </UModal>
</template>
