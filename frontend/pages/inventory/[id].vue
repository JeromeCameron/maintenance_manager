<script setup lang="ts">
import type { Part, EquipmentPart, PartSupplier, StockTransaction } from "~/types"

const route = useRoute()
const router = useRouter()
const {
  getPart, createPart, updatePart,
  getCategories,
  getEquipmentPartsByPart, createEquipmentPart, updateEquipmentPart, removeEquipmentPart,
  getPartSuppliersByPart, createPartSupplier, updatePartSupplier, removePartSupplier,
  getStockLevels,
  getTransactions, createTransaction, removeTransaction,
} = useInventory()
const { getAll: getSuppliers } = useSuppliers()
const { getAll: getModels } = useAssetModels()

const isNew = route.params.id === "new"
const partNo = isNew ? null : (route.params.id as string)

const form = ref<Partial<Part>>({
  unit_of_measure: "unit",
  min_level: 0,
  max_level: 100,
  reorder_level: 10,
  reorder_qty: 20,
  is_critical: false,
  is_active: true,
})
const saving = ref(false)
const error = ref<string | null>(null)

const { data: categories } = await useAsyncData("part-cats", () => getCategories())
const { data: suppliers } = await useAsyncData("all-suppliers", () => getSuppliers())
const { data: assetModels } = await useAsyncData("all-asset-models", () => getModels())

const stockLevels = ref<{ id?: number; location_id?: number; quantity: number }[]>([])
const transactions = ref<StockTransaction[]>([])
const equipmentParts = ref<EquipmentPart[]>([])
const partSuppliers = ref<PartSupplier[]>([])

if (!isNew && partNo) {
  const [part, allStock, allTx, ep, ps] = await Promise.all([
    getPart(partNo),
    getStockLevels(),
    getTransactions(),
    getEquipmentPartsByPart(partNo),
    getPartSuppliersByPart(partNo),
  ])
  form.value = { ...part }
  stockLevels.value = (allStock ?? []).filter((s) => s.part_no === partNo)
  transactions.value = (allTx ?? []).filter((t) => t.part_no === partNo).slice(0, 20)
  equipmentParts.value = ep ?? []
  partSuppliers.value = ps ?? []
}

const categoryOptions = computed(() =>
  (categories.value ?? []).map((c) => ({ label: c.name, value: c.id }))
)
const supplierOptions = computed(() =>
  (suppliers.value ?? []).map((s) => ({ label: s.name, value: s.supplier_id }))
)
const modelOptions = computed(() =>
  (assetModels.value ?? []).map((m) => ({ label: `${m.model_no} — ${m.manufacturer}`, value: m.model_no }))
)

const uomOptions = ["unit", "pieces", "gallons", "drums", "boxes", "pairs", "quart", "liter", "meter", "bag"]

async function save() {
  saving.value = true
  error.value = null
  try {
    if (isNew) {
      await createPart(form.value as Part)
      router.push("/inventory")
    } else {
      await updatePart(partNo!, form.value as Part)
    }
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    saving.value = false
  }
}

// ── Stock adjustment ──────────────────────────────────────────
const adjustment = ref<Partial<StockTransaction>>({ transaction_type: "adjust", quantity: 0 })
const adjusting = ref(false)

async function submitAdjustment() {
  if (!partNo) return
  adjusting.value = true
  try {
    const tx = await createTransaction({
      ...adjustment.value,
      part_no: partNo,
      transaction_date: new Date().toISOString().slice(0, 10),
    } as StockTransaction)
    transactions.value = [tx, ...transactions.value]
    adjustment.value = { transaction_type: "adjust", quantity: 0 }
  } finally {
    adjusting.value = false
  }
}

async function deleteTransaction(id: number) {
  await removeTransaction(id)
  transactions.value = transactions.value.filter((t) => t.id !== id)
}

const txColumns = [
  { accessorKey: "transaction_date", header: "Date" },
  { accessorKey: "transaction_type", header: "Type" },
  { accessorKey: "quantity", header: "Qty" },
  { accessorKey: "notes", header: "Notes" },
  { id: "actions", header: "" },
]

const txTypeColors: Record<string, string> = { receive: "success", issue: "warning", adjust: "info" }

// ── Equipment Parts ───────────────────────────────────────────
const showEpModal = ref(false)
const epEditing = ref<EquipmentPart | null>(null)
const epForm = ref<Partial<EquipmentPart>>({})
const savingEp = ref(false)
const epError = ref<string | null>(null)

function openCreateEp() {
  epEditing.value = null
  epForm.value = { part_no: partNo ?? undefined, is_critical: false }
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
      equipmentParts.value = equipmentParts.value.map((e) => e.id === updated.id ? updated : e)
    } else {
      const created = await createEquipmentPart(epForm.value as EquipmentPart)
      equipmentParts.value = [...equipmentParts.value, created]
    }
    showEpModal.value = false
  } catch (e: unknown) {
    epError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingEp.value = false
  }
}

async function deleteEp(id: number) {
  await removeEquipmentPart(id)
  equipmentParts.value = equipmentParts.value.filter((e) => e.id !== id)
}

const epColumns = [
  { accessorKey: "model_no", header: "Model No." },
  { accessorKey: "is_critical", header: "Critical" },
  { id: "actions", header: "" },
]

// ── Part Suppliers ────────────────────────────────────────────
const showPsModal = ref(false)
const psEditing = ref<PartSupplier | null>(null)
const psForm = ref<Partial<PartSupplier>>({})
const savingPs = ref(false)
const psError = ref<string | null>(null)

function openCreatePs() {
  psEditing.value = null
  psForm.value = { part_no: partNo ?? undefined }
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
      partSuppliers.value = partSuppliers.value.map((p) => p.id === updated.id ? updated : p)
    } else {
      const created = await createPartSupplier(psForm.value as PartSupplier)
      partSuppliers.value = [...partSuppliers.value, created]
    }
    showPsModal.value = false
  } catch (e: unknown) {
    psError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingPs.value = false
  }
}

async function deletePs(id: number) {
  await removePartSupplier(id)
  partSuppliers.value = partSuppliers.value.filter((p) => p.id !== id)
}

const psColumns = [
  { accessorKey: "supplier_id", header: "Supplier" },
  { accessorKey: "supplier_part_no", header: "Supplier Part No." },
  { accessorKey: "last_cost", header: "Last Cost" },
  { accessorKey: "lead_time_days", header: "Lead (days)" },
  { id: "actions", header: "" },
]
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-3">
      <UButton to="/inventory" variant="ghost" icon="i-heroicons-arrow-left" />
      <h1 class="text-2xl font-bold text-slate-900 dark:text-slate-100">
        {{ isNew ? "New Part" : `Part: ${partNo}` }}
      </h1>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <!-- Part form -->
      <div class="lg:col-span-2">
        <UCard>
          <template #header><h2 class="font-semibold">Part Details</h2></template>
          <form class="grid grid-cols-1 gap-4 sm:grid-cols-2" @submit.prevent="save">
            <UFormField label="Part No" required>
              <UInput v-model="form.part_no" placeholder="e.g. BLT-001" :disabled="!isNew" />
            </UFormField>
            <UFormField label="Part Name" required>
              <UInput v-model="form.part_name" />
            </UFormField>
            <UFormField label="Manufacturer">
              <UInput v-model="form.manufacturer" />
            </UFormField>
            <UFormField label="Category">
              <USelect v-model="form.category_id" :items="categoryOptions" placeholder="Select category" />
            </UFormField>
            <UFormField label="Unit of Measure">
              <USelect v-model="form.unit_of_measure" :items="uomOptions" />
            </UFormField>
            <UFormField label="Last Cost">
              <UInput v-model.number="form.last_cost" type="number" step="0.01" />
            </UFormField>
            <UFormField label="Min Level">
              <UInput v-model.number="form.min_level" type="number" />
            </UFormField>
            <UFormField label="Max Level">
              <UInput v-model.number="form.max_level" type="number" />
            </UFormField>
            <UFormField label="Reorder Level">
              <UInput v-model.number="form.reorder_level" type="number" />
            </UFormField>
            <UFormField label="Reorder Qty">
              <UInput v-model.number="form.reorder_qty" type="number" />
            </UFormField>
            <UFormField label="Critical" class="sm:col-span-1">
              <UCheckbox v-model="form.is_critical" label="Critical part" />
            </UFormField>
            <UFormField label="Active" class="sm:col-span-1">
              <UCheckbox v-model="form.is_active" label="Active" />
            </UFormField>
            <UFormField label="Description" class="sm:col-span-2">
              <UTextarea v-model="form.description" :rows="2" />
            </UFormField>
          </form>
          <UAlert v-if="error" color="error" variant="soft" :description="error" class="mt-4" />
          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton to="/inventory" variant="ghost">Cancel</UButton>
              <UButton :loading="saving" @click="save">{{ isNew ? "Create Part" : "Save Changes" }}</UButton>
            </div>
          </template>
        </UCard>
      </div>

      <!-- Sidebar -->
      <div v-if="!isNew" class="space-y-4">
        <UCard>
          <template #header><h2 class="font-semibold">Stock Levels</h2></template>
          <div class="space-y-2 text-sm">
            <div v-for="s in stockLevels" :key="s.id" class="flex justify-between">
              <span class="text-gray-500 dark:text-slate-400">Location {{ s.location_id ?? "—" }}</span>
              <span class="font-semibold">{{ s.quantity }}</span>
            </div>
            <p v-if="!stockLevels.length" class="text-gray-400 dark:text-slate-500">No stock recorded.</p>
          </div>
        </UCard>

        <UCard>
          <template #header><h2 class="font-semibold">Stock Adjustment</h2></template>
          <div class="space-y-3">
            <UFormField label="Type">
              <USelect v-model="adjustment.transaction_type" :items="['receive', 'issue', 'adjust']" />
            </UFormField>
            <UFormField label="Quantity">
              <UInput v-model.number="adjustment.quantity" type="number" />
            </UFormField>
            <UFormField label="Notes">
              <UInput v-model="adjustment.notes" />
            </UFormField>
            <UButton :loading="adjusting" block @click="submitAdjustment">Submit</UButton>
          </div>
        </UCard>
      </div>
    </div>

    <!-- Equipment Parts & Suppliers -->
    <div v-if="!isNew" class="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <!-- Equipment Parts -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="font-semibold">Compatible Equipment</h2>
            <UButton size="xs" leading-icon="i-heroicons-plus" @click="openCreateEp">Add</UButton>
          </div>
        </template>
        <UTable :data="equipmentParts" :columns="epColumns">
          <template #is_critical-cell="{ row: { original: row } }">
            <UBadge v-if="row.is_critical" color="error" variant="soft" size="xs">Critical</UBadge>
            <span v-else class="text-slate-400 dark:text-slate-500 text-sm">—</span>
          </template>
          <template #actions-cell="{ row: { original: row } }">
            <div class="flex items-center gap-1">
              <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEditEp(row)" />
              <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteEp(row.id!)" />
            </div>
          </template>
        </UTable>
        <p v-if="!equipmentParts.length" class="px-2 py-3 text-sm text-slate-400 dark:text-slate-500">No equipment linked.</p>
      </UCard>

      <!-- Part Suppliers -->
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <h2 class="font-semibold">Suppliers</h2>
            <UButton size="xs" leading-icon="i-heroicons-plus" @click="openCreatePs">Add</UButton>
          </div>
        </template>
        <UTable :data="partSuppliers" :columns="psColumns">
          <template #supplier_id-cell="{ row: { original: row } }">
            {{ suppliers?.find(s => s.supplier_id === row.supplier_id)?.name ?? row.supplier_id ?? "—" }}
          </template>
          <template #last_cost-cell="{ row: { original: row } }">
            {{ row.last_cost != null ? `$${row.last_cost.toFixed(2)}` : "—" }}
          </template>
          <template #actions-cell="{ row: { original: row } }">
            <div class="flex items-center gap-1">
              <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEditPs(row)" />
              <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deletePs(row.id!)" />
            </div>
          </template>
        </UTable>
        <p v-if="!partSuppliers.length" class="px-2 py-3 text-sm text-slate-400 dark:text-slate-500">No suppliers linked.</p>
      </UCard>
    </div>

    <!-- Transactions -->
    <UCard v-if="!isNew">
      <template #header><h2 class="font-semibold">Recent Transactions</h2></template>
      <UTable :data="transactions" :columns="txColumns">
        <template #transaction_type-cell="{ row: { original: row } }">
          <UBadge :color="txTypeColors[row.transaction_type] ?? 'neutral'" variant="soft" size="xs">
            {{ row.transaction_type }}
          </UBadge>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTransaction(row.id!)" />
        </template>
      </UTable>
    </UCard>

    <!-- Equipment Part Modal -->
    <UModal v-model:open="showEpModal">
      <template #content>
        <div class="w-full max-w-md rounded-xl bg-white dark:bg-slate-900 shadow-xl">
          <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 px-6 py-5">
            <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">{{ epEditing ? "Edit Equipment Link" : "Link Equipment Model" }}</h3>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showEpModal = false" />
          </div>
          <div class="space-y-4 px-6 py-5">
            <UFormField label="Asset Model" required>
              <USelect v-model="epForm.model_no" :items="modelOptions" placeholder="Select model" class="w-full" />
            </UFormField>
            <UFormField label="Critical">
              <UToggle v-model="epForm.is_critical" />
            </UFormField>
          </div>
          <UAlert v-if="epError" color="error" variant="soft" :description="epError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 dark:border-slate-800 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showEpModal = false">Cancel</UButton>
            <UButton :loading="savingEp" @click="saveEp">Save</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Part Supplier Modal -->
    <UModal v-model:open="showPsModal">
      <template #content>
        <div class="w-full max-w-md rounded-xl bg-white dark:bg-slate-900 shadow-xl">
          <div class="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 px-6 py-5">
            <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">{{ psEditing ? "Edit Supplier" : "Add Supplier" }}</h3>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showPsModal = false" />
          </div>
          <div class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
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
          <UAlert v-if="psError" color="error" variant="soft" :description="psError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 dark:border-slate-800 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showPsModal = false">Cancel</UButton>
            <UButton :loading="savingPs" @click="savePs">Save</UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
