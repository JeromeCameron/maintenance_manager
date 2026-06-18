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
const { getParts } = useInventory()

const [{ data: assets }, { data: suppliers }, { data: inventoryParts }] = await Promise.all([
  useAsyncData("wo-modal-assets", () => getAssets()),
  useAsyncData("wo-modal-suppliers", () => getSuppliers()),
  useAsyncData("wo-modal-parts", () => getParts()),
])

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

watch(() => form.value.asset_id, async (id) => {
  form.value.asset_pm_id = undefined
  assetPMs.value = id ? (await getPMsByAsset(id) ?? []) : []
})

// ── Parts ─────────────────────────────────────────────────────
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
  if (!props.workOrderId || !newPart.value.part_no) return
  addingPart.value = true
  try {
    const created = await addPart({ ...newPart.value, work_order_id: props.workOrderId } as WorkOrderPart)
    parts.value = [...parts.value, created]
    newPart.value = { quantity_used: 1 }
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

// ── Load when opened ──────────────────────────────────────────
watch(open, async (val) => {
  if (!val || !props.workOrderId) return
  loading.value = true
  error.value = null
  try {
    const full = await getOne(props.workOrderId)
    form.value = { ...full }
    if (full?.asset_id) assetPMs.value = await getPMsByAsset(full.asset_id) ?? []
    parts.value = await getPartsByWorkOrder(props.workOrderId) ?? []
  } finally { loading.value = false }
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
      <div class="flex max-h-[90vh] w-full max-w-3xl flex-col rounded-xl bg-white shadow-xl">
        <!-- Header -->
        <div class="flex shrink-0 items-center justify-between border-b border-gray-100 px-6 py-5">
          <h3 class="text-base font-semibold text-slate-900">Work Order #{{ workOrderId }}</h3>
          <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="open = false" />
        </div>

        <div v-if="loading" class="flex flex-1 items-center justify-center py-16">
          <UIcon name="i-heroicons-arrow-path" class="h-6 w-6 animate-spin text-gray-400" />
        </div>

        <!-- Scrollable body -->
        <div v-else class="flex-1 overflow-y-auto px-6 py-5 space-y-6">
          <div class="grid grid-cols-2 gap-x-5 gap-y-4">
            <UFormField label="Asset" class="col-span-2">
              <USelect v-model="form.asset_id" :items="assetOptions" placeholder="Select asset…" class="w-full" />
            </UFormField>
            <UFormField label="Supplier">
              <USelect v-model="form.supplier_id" :items="supplierOptions" placeholder="Select supplier…" class="w-full" />
            </UFormField>
            <UFormField label="PM Plan">
              <USelect v-model="form.asset_pm_id" :items="pmOptions" placeholder="Link to PM (optional)" class="w-full" />
            </UFormField>
            <UFormField label="Priority">
              <USelect v-model="form.priority" :items="priorityOptions" class="w-full" />
            </UFormField>
            <UFormField label="Type">
              <USelect v-model="form.typ" :items="typeOptions" class="w-full" />
            </UFormField>
            <UFormField label="Planned / Unplanned">
              <USelect v-model="form.planned" :items="plannedOptions" placeholder="Select…" class="w-full" />
            </UFormField>
            <UFormField label="Status">
              <USelect v-model="form.status" :items="woStatusOptions" class="w-full" />
            </UFormField>
            <UFormField label="Issue Date">
              <UInput v-model="form.issue_date" type="date" class="w-full" />
            </UFormField>
            <UFormField label="Expected Date">
              <UInput v-model="form.expected_date" type="date" class="w-full" />
            </UFormField>
            <UFormField label="Date Completed">
              <UInput v-model="form.date_completed" type="date" class="w-full" />
            </UFormField>
            <UFormField label="Estimated Hours">
              <UInput v-model.number="form.estimated_hours" type="number" step="0.5" class="w-full" />
            </UFormField>
            <UFormField label="Actual Hours">
              <UInput v-model.number="form.actual_hours" type="number" step="0.5" class="w-full" />
            </UFormField>
            <UFormField label="Estimated Cost ($)">
              <UInput v-model.number="form.estimated_cost" type="number" step="0.01" class="w-full" />
            </UFormField>
            <UFormField label="Actual Cost ($)">
              <UInput v-model.number="form.actual_cost" type="number" step="0.01" class="w-full" />
            </UFormField>
            <UFormField label="Description" class="col-span-2">
              <UTextarea v-model="form.description" :rows="3" class="w-full" />
            </UFormField>
            <UFormField label="Notes" class="col-span-2">
              <UTextarea v-model="form.notes" :rows="2" class="w-full" />
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
                  <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deletePart(row.id)" />
                </div>
              </template>
            </UTable>

            <div v-if="editingPart" class="mt-3 grid grid-cols-5 gap-3 rounded-lg border border-primary-200 bg-primary-50 p-3">
              <UFormField label="Part No" class="col-span-2">
                <USelect v-model="editPartDraft.part_no" :items="partOptions" placeholder="Select part…" class="w-full" />
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

            <div v-else class="mt-3 grid grid-cols-5 gap-3 border-t pt-3">
              <UFormField label="Part No" class="col-span-2">
                <USelect v-model="newPart.part_no" :items="partOptions" placeholder="Select part…" class="w-full" />
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

          <UAlert v-if="error" color="error" variant="soft" :description="error" />
        </div>

        <!-- Footer -->
        <div class="flex shrink-0 items-center justify-end gap-3 border-t border-gray-100 px-6 py-4">
          <UButton variant="ghost" color="neutral" @click="open = false">Cancel</UButton>
          <UButton :loading="saving" @click="save">Save Changes</UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>
