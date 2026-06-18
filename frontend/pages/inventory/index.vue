<script setup lang="ts">
import type { Part, EquipmentPart, PartSupplier, StockTransaction, StockLevel, WorkOrder, PurchaseOrder } from "~/types"

const { isAdmin, user } = useAuth()
const {
  getParts, getPart, createPart, updatePart, removePart,
  getCategories, getStockLevels,
  getEquipmentPartsByPart, createEquipmentPart, updateEquipmentPart, removeEquipmentPart,
  getPartSuppliersByPart, createPartSupplier, updatePartSupplier, removePartSupplier,
  getTransactions, createTransaction, removeTransaction,
} = useInventory()
const { getAll: getSuppliers } = useSuppliers()
const { getAll: getAssetModels } = useAssetModels()
const { getAll: getLocations } = useLocations()
const { getPOs } = useFinance()
const { get: apiGet } = useApi()

const { data: parts, refresh } = await useAsyncData("parts", () => getParts())
const { data: categories } = await useAsyncData("part-cats", () => getCategories())
const { data: allStockLevels, refresh: refreshStock } = await useAsyncData("stock-levels", () => getStockLevels())
const { data: suppliers } = await useAsyncData("all-suppliers", () => getSuppliers())
const { data: assetModels } = await useAsyncData("all-asset-models", () => getAssetModels())
const { data: locations } = await useAsyncData("locations", () => getLocations())
const { data: purchaseOrders } = await useAsyncData("pos", () => getPOs())
const { data: workOrders } = await useAsyncData("work-orders", () => apiGet<WorkOrder[]>("/work-orders"))

const catMap = computed(() => {
  const m: Record<number, string> = {}
  for (const c of categories.value ?? []) { if (c.id != null) m[c.id] = c.name }
  return m
})

const stockMap = computed(() => {
  const m: Record<string, number> = {}
  for (const s of allStockLevels.value ?? []) { if (s.part_no) m[s.part_no] = (m[s.part_no] ?? 0) + s.quantity }
  return m
})

const locationMap = computed(() => {
  const m: Record<number, string> = {}
  for (const l of locations.value ?? []) { if (l.location_id != null) m[l.location_id] = l.name }
  return m
})

const categoryOptions = computed(() => (categories.value ?? []).map(c => ({ label: c.name, value: c.id })))
const supplierOptions = computed(() => (suppliers.value ?? []).map(s => ({ label: s.name, value: s.supplier_id })))
const modelOptions = computed(() => (assetModels.value ?? []).map(m => ({ label: `${m.model_no} — ${m.manufacturer}`, value: m.model_no })))
const locationOptions = computed(() => [
  { label: "— No location —", value: null },
  ...(locations.value ?? []).map(l => ({ label: `${l.name} (${l.parish})`, value: l.location_id })),
])
const poOptions = computed(() => [
  { label: "— None —", value: null },
  ...(purchaseOrders.value ?? []).map(p => ({ label: p.po_no, value: p.po_no })),
])
const workOrderOptions = computed(() => [
  { label: "— None —", value: null },
  ...[...(workOrders.value ?? [])]
    .sort((a, b) => (a.work_order_id ?? 0) - (b.work_order_id ?? 0))
    .map(w => ({ label: `WO-${w.work_order_id}${w.description ? ` — ${w.description}` : ""}`, value: w.work_order_id })),
])
const uomOptions = ["unit", "pieces", "gallons", "drums", "boxes", "pairs", "quart", "liter", "meter", "bag"]

const search = ref("")
const filtered = computed(() =>
  (parts.value ?? []).filter(p => {
    const q = search.value.toLowerCase()
    return !q || p.part_no.toLowerCase().includes(q) || p.part_name.toLowerCase().includes(q)
  })
)
const lowStock = computed(() => (parts.value ?? []).filter(p => (stockMap.value[p.part_no] ?? 0) <= p.reorder_level))

const columns = [
  { accessorKey: "part_no", header: "Part No" },
  { accessorKey: "part_name", header: "Name" },
  { accessorKey: "manufacturer", header: "Manufacturer" },
  { accessorKey: "category_id", header: "Category" },
  { accessorKey: "unit_of_measure", header: "UOM" },
  { id: "stock", header: "Stock" },
  { accessorKey: "reorder_level", header: "Reorder At" },
  { accessorKey: "is_critical", header: "Critical" },
  { id: "actions", header: "" },
]

// ── Part modal ────────────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const activeTab = ref("details")
const saving = ref(false)
const formError = ref<string | null>(null)
const loadingPart = ref(false)

const partStockLevels = ref<StockLevel[]>([])
const partTransactions = ref<StockTransaction[]>([])
const partEquipment = ref<EquipmentPart[]>([])
const partSupplierRows = ref<PartSupplier[]>([])

const defaultForm = (): Partial<Part> => ({
  unit_of_measure: "unit", min_level: 0, max_level: 100,
  reorder_level: 10, reorder_qty: 20, is_critical: false, is_active: true,
})
const form = ref<Partial<Part>>(defaultForm())

const partTabs = computed(() => [
  { label: "Details", value: "details", icon: "i-heroicons-document-text" },
  ...(isEditing.value ? [
    { label: "Stock Levels", value: "stock", icon: "i-heroicons-cube" },
    { label: "Transactions", value: "transactions", icon: "i-heroicons-arrow-path" },
    { label: "Compatible Equipment", value: "equipment", icon: "i-heroicons-wrench-screwdriver" },
    { label: "Suppliers", value: "suppliers", icon: "i-heroicons-truck" },
  ] : []),
])

function openCreate() {
  form.value = defaultForm()
  isEditing.value = false
  activeTab.value = "details"
  formError.value = null
  partStockLevels.value = []
  partTransactions.value = []
  partEquipment.value = []
  partSupplierRows.value = []
  showModal.value = true
}

async function openEdit(partNo: string) {
  form.value = defaultForm()
  isEditing.value = true
  activeTab.value = "details"
  formError.value = null
  loadingPart.value = true
  showModal.value = true
  try {
    const [part, allTx, ep, ps] = await Promise.all([
      getPart(partNo),
      getTransactions(),
      getEquipmentPartsByPart(partNo),
      getPartSuppliersByPart(partNo),
    ])
    form.value = { ...part }
    partStockLevels.value = (allStockLevels.value ?? []).filter(s => s.part_no === partNo)
    partTransactions.value = (allTx ?? []).filter(t => t.part_no === partNo).slice(0, 20)
    partEquipment.value = ep ?? []
    partSupplierRows.value = ps ?? []
  } finally {
    loadingPart.value = false
  }
}

async function save() {
  saving.value = true
  formError.value = null
  try {
    if (isEditing.value && form.value.part_no) {
      await updatePart(form.value.part_no, form.value as Part)
    } else {
      await createPart(form.value as Part)
    }
    await refresh()
    showModal.value = false
  } catch (e: unknown) {
    formError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    saving.value = false
  }
}

const totalStockQty = computed(() => partStockLevels.value.reduce((sum, s) => sum + s.quantity, 0))

// ── Stock & Transactions ──────────────────────────────────────
const defaultAdjustment = (): Partial<StockTransaction> => ({
  transaction_type: "receive",
  quantity: 1,
  transaction_date: new Date().toISOString().slice(0, 10),
  entered_by: user.value?.user_id ?? undefined,
  location_id: undefined,
  work_order_id: undefined,
  po_no: undefined,
  notes: undefined,
})
const adjustment = ref<Partial<StockTransaction>>(defaultAdjustment())
const adjusting = ref(false)

async function submitAdjustment() {
  if (!form.value.part_no) return
  adjusting.value = true
  try {
    const tx = await createTransaction({
      ...adjustment.value,
      part_no: form.value.part_no,
    } as StockTransaction)
    partTransactions.value = [tx, ...partTransactions.value]
    await refreshStock()
    partStockLevels.value = (allStockLevels.value ?? []).filter(s => s.part_no === form.value.part_no)
    adjustment.value = defaultAdjustment()
  } finally {
    adjusting.value = false
  }
}

// ── Generic confirm modal ─────────────────────────────────────
const pendingDelete = ref<{ label: string; action: () => Promise<void> } | null>(null)
const confirmingDelete = ref(false)
const showConfirmDeleteModal = computed({ get: () => !!pendingDelete.value, set: (v) => { if (!v) pendingDelete.value = null } })

async function runPendingDelete() {
  if (!pendingDelete.value) return
  confirmingDelete.value = true
  try {
    await pendingDelete.value.action()
    pendingDelete.value = null
  } finally {
    confirmingDelete.value = false
  }
}

async function deleteTransaction(id: number) {
  pendingDelete.value = {
    label: "this transaction",
    action: async () => {
      await removeTransaction(id)
      partTransactions.value = partTransactions.value.filter(t => t.id !== id)
      await refreshStock()
      partStockLevels.value = (allStockLevels.value ?? []).filter(s => s.part_no === form.value.part_no)
    },
  }
}

const txColumns = [
  { accessorKey: "transaction_date", header: "Date" },
  { accessorKey: "transaction_type", header: "Type" },
  { accessorKey: "quantity", header: "Qty" },
  { accessorKey: "notes", header: "Notes" },
  { id: "actions", header: "" },
]
const txTypeColors: Record<string, string> = { receive: "success", issue: "warning", adjust: "info" }

// ── Compatible Equipment ──────────────────────────────────────
const showEpModal = ref(false)
const epEditing = ref<EquipmentPart | null>(null)
const epForm = ref<Partial<EquipmentPart>>({})
const savingEp = ref(false)
const epError = ref<string | null>(null)

function openCreateEp() {
  epEditing.value = null
  epForm.value = { part_no: form.value.part_no ?? undefined, is_critical: false }
  epError.value = null
  showEpModal.value = true
}

function openEditEp(row: EquipmentPart) {
  epEditing.value = row
  epForm.value = { ...row }
  epError.value = null
  showEpModal.value = true
}

async function saveEp() {
  savingEp.value = true
  epError.value = null
  try {
    if (epEditing.value?.id) {
      const updated = await updateEquipmentPart(epEditing.value.id, epForm.value as EquipmentPart)
      partEquipment.value = partEquipment.value.map(e => e.id === updated.id ? updated : e)
    } else {
      const created = await createEquipmentPart(epForm.value as EquipmentPart)
      partEquipment.value = [...partEquipment.value, created]
    }
    showEpModal.value = false
  } catch (e: unknown) {
    epError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingEp.value = false
  }
}

async function deleteEp(id: number) {
  pendingDelete.value = {
    label: "this equipment link",
    action: async () => {
      await removeEquipmentPart(id)
      partEquipment.value = partEquipment.value.filter(e => e.id !== id)
    },
  }
}

const epColumns = [
  { accessorKey: "model_no", header: "Model No." },
  { accessorKey: "is_critical", header: "Critical" },
  { id: "actions", header: "" },
]

// ── Suppliers ─────────────────────────────────────────────────
const showPsModal = ref(false)
const psEditing = ref<PartSupplier | null>(null)
const psForm = ref<Partial<PartSupplier>>({})
const savingPs = ref(false)
const psError = ref<string | null>(null)

function openCreatePs() {
  psEditing.value = null
  psForm.value = { part_no: form.value.part_no ?? undefined }
  psError.value = null
  showPsModal.value = true
}

function openEditPs(row: PartSupplier) {
  psEditing.value = row
  psForm.value = { ...row }
  psError.value = null
  showPsModal.value = true
}

async function savePs() {
  savingPs.value = true
  psError.value = null
  try {
    if (psEditing.value?.id) {
      const updated = await updatePartSupplier(psEditing.value.id, psForm.value as PartSupplier)
      partSupplierRows.value = partSupplierRows.value.map(p => p.id === updated.id ? updated : p)
    } else {
      const created = await createPartSupplier(psForm.value as PartSupplier)
      partSupplierRows.value = [...partSupplierRows.value, created]
    }
    showPsModal.value = false
  } catch (e: unknown) {
    psError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingPs.value = false
  }
}

async function deletePs(id: number) {
  pendingDelete.value = {
    label: "this supplier link",
    action: async () => {
      await removePartSupplier(id)
      partSupplierRows.value = partSupplierRows.value.filter(p => p.id !== id)
    },
  }
}

const psColumns = [
  { accessorKey: "supplier_id", header: "Supplier" },
  { accessorKey: "supplier_part_no", header: "Supplier Part No." },
  { accessorKey: "last_cost", header: "Last Cost" },
  { accessorKey: "lead_time_days", header: "Lead (days)" },
  { id: "actions", header: "" },
]

// ── Delete Part ───────────────────────────────────────────────
function deletePart(part: Part) {
  pendingDelete.value = {
    label: `part ${part.part_no}`,
    action: async () => {
      await removePart(part.part_no)
      await refresh()
      showModal.value = false
    },
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <UButton leading-icon="i-heroicons-plus" @click="openCreate">New Part</UButton>
    </div>

    <UAlert v-if="lowStock.length" color="warning" variant="soft" icon="i-heroicons-exclamation-triangle"
      :title="`${lowStock.length} part${lowStock.length > 1 ? 's' : ''} at or below reorder level`" />

    <UCard>
      <template #header>
        <UInput v-model="search" placeholder="Search by part no or name..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
      </template>
      <UTable :data="filtered" :columns="columns" :ui="{ root: 'relative overflow-auto max-h-[calc(100vh-22rem)]' }">
        <template #category_id-cell="{ row: { original: row } }">{{ catMap[row.category_id] ?? "—" }}</template>
        <template #stock-cell="{ row: { original: row } }">
          <span :class="(stockMap[row.part_no] ?? 0) <= row.reorder_level ? 'font-semibold text-amber-600' : 'font-medium'">
            {{ stockMap[row.part_no] ?? 0 }}
          </span>
        </template>
        <template #is_critical-cell="{ row: { original: row } }">
          <UBadge v-if="row.is_critical" color="error" variant="soft" size="sm">Critical</UBadge>
          <span v-else class="text-slate-400">—</span>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-eye" @click="openEdit(row.part_no)" />
            <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deletePart(row)" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Part Modal -->
    <UModal v-model:open="showModal" :ui="{ content: 'max-w-5xl' }">
      <template #content>
        <div class="flex h-[85vh] max-h-[800px] w-full flex-col rounded-xl bg-white shadow-xl">
          <!-- Header -->
          <div class="flex shrink-0 items-start gap-4 border-b border-slate-100 px-6 py-5">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50">
              <UIcon name="i-heroicons-archive-box" class="h-5 w-5 text-blue-600" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-3">
                <h3 class="text-base font-semibold text-slate-900">
                  {{ isEditing ? `${form.part_no} — ${form.part_name ?? ""}` : "New Part" }}
                </h3>
                <UBadge v-if="isEditing" :color="totalStockQty <= (form.reorder_level ?? 0) ? 'warning' : 'success'" variant="soft" size="sm">
                  {{ totalStockQty }} {{ form.unit_of_measure ?? "units" }} in stock
                </UBadge>
              </div>
              <p class="text-sm text-slate-500">{{ isEditing ? "View and manage part details" : "Add a new part to inventory" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>

          <!-- Tabs -->
          <div v-if="isEditing" class="shrink-0 flex gap-0 border-b border-slate-200 px-6">
            <button v-for="tab in partTabs" :key="tab.value"
              class="flex items-center gap-1.5 border-b-2 px-4 py-3 text-sm font-medium transition-colors"
              :class="activeTab === tab.value
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'"
              @click="activeTab = tab.value">
              <UIcon :name="tab.icon" class="h-4 w-4" />
              {{ tab.label }}
            </button>
          </div>

          <!-- Loading -->
          <div v-if="loadingPart" class="flex flex-1 items-center justify-center">
            <UIcon name="i-heroicons-arrow-path" class="h-6 w-6 animate-spin text-slate-400" />
          </div>

          <!-- Tab content -->
          <div v-else class="min-h-0 flex-1 overflow-y-auto px-6 py-5">

            <!-- Details Tab -->
            <div v-if="activeTab === 'details'" class="grid grid-cols-2 gap-x-5 gap-y-4">
              <UFormField label="Part No" required>
                <UInput v-model="form.part_no" placeholder="e.g. BLT-001" :disabled="isEditing" class="w-full" />
              </UFormField>
              <UFormField label="Part Name" required>
                <UInput v-model="form.part_name" class="w-full" />
              </UFormField>
              <UFormField label="Manufacturer">
                <UInput v-model="form.manufacturer" class="w-full" />
              </UFormField>
              <UFormField label="Category">
                <USelect v-model="form.category_id" :items="categoryOptions" placeholder="Select category" class="w-full" />
              </UFormField>
              <UFormField label="Unit of Measure">
                <USelect v-model="form.unit_of_measure" :items="uomOptions" class="w-full" />
              </UFormField>
              <UFormField label="Last Cost">
                <UInput v-model.number="form.last_cost" type="number" step="0.01" class="w-full" />
              </UFormField>
              <UFormField label="Min Level">
                <UInput v-model.number="form.min_level" type="number" class="w-full" />
              </UFormField>
              <UFormField label="Max Level">
                <UInput v-model.number="form.max_level" type="number" class="w-full" />
              </UFormField>
              <UFormField label="Reorder Level">
                <UInput v-model.number="form.reorder_level" type="number" class="w-full" />
              </UFormField>
              <UFormField label="Reorder Qty">
                <UInput v-model.number="form.reorder_qty" type="number" class="w-full" />
              </UFormField>
              <UFormField label="Critical">
                <UCheckbox v-model="form.is_critical" label="Critical part" />
              </UFormField>
              <UFormField label="Active">
                <UCheckbox v-model="form.is_active" label="Active" />
              </UFormField>
              <UFormField label="Description" class="col-span-2">
                <UTextarea v-model="form.description" :rows="3" class="w-full" />
              </UFormField>
              <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="col-span-2" />
            </div>

            <!-- Stock Levels Tab -->
            <div v-else-if="activeTab === 'stock'">
              <div v-if="partStockLevels.length" class="divide-y divide-slate-100 rounded-lg border border-slate-200">
                <div v-for="s in partStockLevels" :key="s.id" class="flex items-center justify-between px-4 py-3">
                  <span class="text-sm text-slate-600">
                    {{ s.location_id != null ? (locationMap[s.location_id] ?? `Location ${s.location_id}`) : "No location" }}
                  </span>
                  <span class="text-sm font-semibold" :class="s.quantity <= (form.reorder_level ?? 0) ? 'text-amber-600' : 'text-slate-900'">
                    {{ s.quantity }} {{ form.unit_of_measure }}
                  </span>
                </div>
              </div>
              <p v-else class="text-sm text-slate-400">No stock recorded.</p>
            </div>

            <!-- Transactions Tab -->
            <div v-else-if="activeTab === 'transactions'" class="space-y-6">
              <!-- Record transaction form -->
              <div class="rounded-lg border border-slate-200 p-4">
                <h4 class="mb-3 text-sm font-semibold text-slate-700">Record Transaction</h4>
                <div class="grid grid-cols-3 gap-x-4 gap-y-3">
                  <UFormField label="Type">
                    <USelect v-model="adjustment.transaction_type" :items="['receive', 'issue', 'adjust']" class="w-full" />
                  </UFormField>
                  <UFormField label="Quantity">
                    <UInput v-model.number="adjustment.quantity" type="number" min="1" class="w-full" />
                  </UFormField>
                  <UFormField label="Date">
                    <UInput v-model="adjustment.transaction_date" type="date" class="w-full" />
                  </UFormField>
                  <UFormField label="Location">
                    <USelect v-model="adjustment.location_id" :items="locationOptions" class="w-full" />
                  </UFormField>
                  <UFormField label="Work Order">
                    <USelect v-model="adjustment.work_order_id" :items="workOrderOptions" searchable searchable-placeholder="Type WO number…" class="w-full" />
                  </UFormField>
                  <UFormField label="Purchase Order">
                    <USelect v-model="adjustment.po_no" :items="poOptions" class="w-full" />
                  </UFormField>
                  <UFormField label="Entered By">
                    <UInput :value="`${user?.firstname ?? ''} ${user?.lastname ?? ''}`.trim() || user?.username" disabled class="w-full" />
                  </UFormField>
                  <UFormField label="Notes" class="col-span-2">
                    <UInput v-model="adjustment.notes" placeholder="Optional notes" class="w-full" />
                  </UFormField>
                </div>
                <div class="mt-3 flex justify-end">
                  <UButton :loading="adjusting" @click="submitAdjustment">Submit Transaction</UButton>
                </div>
              </div>

              <!-- Transactions history -->
              <div>
                <h4 class="mb-3 text-sm font-semibold text-slate-700">Recent Transactions</h4>
                <UTable :data="partTransactions" :columns="txColumns">
                  <template #transaction_type-cell="{ row: { original: row } }">
                    <UBadge :color="txTypeColors[row.transaction_type] ?? 'neutral'" variant="soft" size="xs">
                      {{ row.transaction_type }}
                    </UBadge>
                  </template>
                  <template #actions-cell="{ row: { original: row } }">
                    <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTransaction(row.id!)" />
                  </template>
                </UTable>
                <p v-if="!partTransactions.length" class="mt-2 text-sm text-slate-400">No transactions recorded.</p>
              </div>
            </div>

            <!-- Compatible Equipment Tab -->
            <div v-else-if="activeTab === 'equipment'">
              <div class="mb-3 flex items-center justify-between">
                <h4 class="text-sm font-semibold text-slate-700">Compatible Equipment Models</h4>
                <UButton size="xs" leading-icon="i-heroicons-plus" @click="openCreateEp">Add</UButton>
              </div>
              <UTable :data="partEquipment" :columns="epColumns">
                <template #is_critical-cell="{ row: { original: row } }">
                  <UBadge v-if="row.is_critical" color="error" variant="soft" size="xs">Critical</UBadge>
                  <span v-else class="text-slate-400 text-sm">—</span>
                </template>
                <template #actions-cell="{ row: { original: row } }">
                  <div class="flex items-center gap-1">
                    <UButton variant="ghost" size="xs" icon="i-heroicons-eye" @click="openEditEp(row)" />
                    <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteEp(row.id!)" />
                  </div>
                </template>
              </UTable>
              <p v-if="!partEquipment.length" class="mt-2 text-sm text-slate-400">No equipment linked.</p>
            </div>

            <!-- Suppliers Tab -->
            <div v-else-if="activeTab === 'suppliers'">
              <div class="mb-3 flex items-center justify-between">
                <h4 class="text-sm font-semibold text-slate-700">Part Suppliers</h4>
                <UButton size="xs" leading-icon="i-heroicons-plus" @click="openCreatePs">Add</UButton>
              </div>
              <UTable :data="partSupplierRows" :columns="psColumns">
                <template #supplier_id-cell="{ row: { original: row } }">
                  {{ suppliers?.find(s => s.supplier_id === row.supplier_id)?.name ?? row.supplier_id ?? "—" }}
                </template>
                <template #last_cost-cell="{ row: { original: row } }">
                  {{ row.last_cost != null ? `$${row.last_cost.toFixed(2)}` : "—" }}
                </template>
                <template #actions-cell="{ row: { original: row } }">
                  <div class="flex items-center gap-1">
                    <UButton variant="ghost" size="xs" icon="i-heroicons-eye" @click="openEditPs(row)" />
                    <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deletePs(row.id!)" />
                  </div>
                </template>
              </UTable>
              <p v-if="!partSupplierRows.length" class="mt-2 text-sm text-slate-400">No suppliers linked.</p>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex shrink-0 justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showModal = false">
              {{ activeTab === 'details' ? 'Cancel' : 'Close' }}
            </UButton>
            <UButton v-if="activeTab === 'details'" :loading="saving" @click="save">
              {{ isEditing ? "Save Changes" : "Create Part" }}
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Equipment Model Modal -->
    <UModal v-model:open="showEpModal">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <h3 class="font-semibold">{{ epEditing ? "Edit Equipment Link" : "Link Equipment Model" }}</h3>
              <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showEpModal = false" />
            </div>
          </template>
          <div class="space-y-4">
            <UFormField label="Asset Model" required>
              <USelect v-model="epForm.model_no" :items="modelOptions" placeholder="Select model" class="w-full" />
            </UFormField>
            <UFormField label="Critical">
              <UCheckbox v-model="epForm.is_critical" label="Critical part for this equipment" />
            </UFormField>
          </div>
          <UAlert v-if="epError" color="error" variant="soft" :description="epError" class="mt-4" />
          <template #footer>
            <div class="flex justify-end gap-3">
              <UButton variant="ghost" color="neutral" @click="showEpModal = false">Cancel</UButton>
              <UButton :loading="savingEp" @click="saveEp">Save</UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <!-- Supplier Modal -->
    <UModal v-model:open="showPsModal">
      <template #content>
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <h3 class="font-semibold">{{ psEditing ? "Edit Supplier" : "Add Supplier" }}</h3>
              <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showPsModal = false" />
            </div>
          </template>
          <div class="grid grid-cols-2 gap-x-5 gap-y-4">
            <UFormField label="Supplier" required class="col-span-2">
              <USelect v-model="psForm.supplier_id" :items="supplierOptions" placeholder="Select supplier" class="w-full" />
            </UFormField>
            <UFormField label="Supplier Part No.">
              <UInput v-model="psForm.supplier_part_no" class="w-full" />
            </UFormField>
            <UFormField label="Last Cost">
              <UInput v-model.number="psForm.last_cost" type="number" step="0.01" class="w-full" />
            </UFormField>
            <UFormField label="Lead Time (days)">
              <UInput v-model.number="psForm.lead_time_days" type="number" class="w-full" />
            </UFormField>
          </div>
          <UAlert v-if="psError" color="error" variant="soft" :description="psError" class="mt-4" />
          <template #footer>
            <div class="flex justify-end gap-3">
              <UButton variant="ghost" color="neutral" @click="showPsModal = false">Cancel</UButton>
              <UButton :loading="savingPs" @click="savePs">Save</UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <!-- Generic Delete Confirmation -->
    <UModal v-model:open="showConfirmDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Confirm Delete</h3></template>
          <p class="text-sm text-slate-500">Delete <strong>{{ pendingDelete?.label }}</strong>? This cannot be undone.</p>
          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton variant="ghost" @click="pendingDelete = null">Cancel</UButton>
              <UButton color="error" :loading="confirmingDelete" @click="runPendingDelete">Delete</UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
  </div>
</template>
