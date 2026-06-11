<script setup lang="ts">
import type { PurchaseOrder, Invoice, Budget } from "~/types"

const { getPOs, getPO, createPO, updatePO, removePO, getInvoices, getInvoice, createInvoice, updateInvoice, removeInvoice, getBudgets, createBudget, updateBudget, removeBudget, getCostCentres } = useFinance()
const { getAll: getAssets } = useAssets()
const { getAll: getSuppliers } = useSuppliers()
const { getAll: getLocations } = useLocations()

const [{ data: pos, refresh: refreshPOs }, { data: invoices, refresh: refreshInvoices }, { data: budgets, refresh: refreshBudgets }, { data: assets }, { data: suppliers }, { data: locations }, { data: costCentres }] = await Promise.all([
  useAsyncData("pos", () => getPOs()),
  useAsyncData("invoices", () => getInvoices()),
  useAsyncData("budgets", () => getBudgets()),
  useAsyncData("assets-select", () => getAssets()),
  useAsyncData("suppliers-select", () => getSuppliers()),
  useAsyncData("locations-select", () => getLocations()),
  useAsyncData("cost-centres", () => getCostCentres()),
])

const activeTab = ref("pos")

const poColumns = [
  { accessorKey: "po_no", header: "PO No" },
  { accessorKey: "po_date", header: "Date" },
  { accessorKey: "asset_id", header: "Asset" },
  { accessorKey: "po_type", header: "Type" },
  { accessorKey: "subtotal", header: "Subtotal" },
  { id: "actions", header: "" },
]

const invoiceColumns = [
  { accessorKey: "invoice_no", header: "Invoice No" },
  { accessorKey: "job_date", header: "Job Date" },
  { accessorKey: "asset_id", header: "Asset" },
  { accessorKey: "invoice_type", header: "Type" },
  { accessorKey: "status", header: "Status" },
  { accessorKey: "subtotal", header: "Subtotal" },
  { id: "actions", header: "" },
]

const budgetColumns = [
  { accessorKey: "gl_code", header: "GL Code" },
  { accessorKey: "financial_year", header: "FY" },
  { accessorKey: "month", header: "Month" },
  { accessorKey: "amount", header: "Amount" },
  { accessorKey: "notes", header: "Notes" },
  { id: "actions", header: "" },
]

const invoiceStatusColors: Record<string, string> = { processing: "info", submitted: "success", on_hold: "warning" }

const search = ref("")
const filteredPOs = computed(() =>
  (pos.value ?? []).filter((p) => !search.value || p.po_no.toLowerCase().includes(search.value.toLowerCase()) || (p.asset_id ?? "").toLowerCase().includes(search.value.toLowerCase()))
)
const filteredInvoices = computed(() =>
  (invoices.value ?? []).filter((i) => !search.value || i.invoice_no.toLowerCase().includes(search.value.toLowerCase()) || (i.asset_id ?? "").toLowerCase().includes(search.value.toLowerCase()))
)
const totalPOValue = computed(() => (pos.value ?? []).reduce((s, p) => s + p.subtotal, 0))
const totalInvoiceValue = computed(() => (invoices.value ?? []).reduce((s, i) => s + i.subtotal, 0))

// ── Shared options ────────────────────────────────────────────
const assetOptions = computed(() => (assets.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id })))
const supplierOptions = computed(() => (suppliers.value ?? []).map((s) => ({ label: s.name, value: s.supplier_id })))
const locationOptions = computed(() => (locations.value ?? []).map((l) => ({ label: l.name, value: l.location_id })))
const costCentreOptions = computed(() => (costCentres.value ?? []).map((c) => ({ label: `${c.gl_code}${c.description ? ` — ${c.description}` : ""}`, value: c.gl_code })))
const poTypeOptions = ["corrective", "predictive", "preventative", "consumables", "rental"]
const invoiceStatusOptions = ["processing", "submitted", "on_hold"]
const invoiceTypeOptions = ["parts", "parts_and_labour", "labour", "consumables", "services"]
const monthOptions = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

// ── PO Modal ──────────────────────────────────────────────────
const showPOModal = ref(false)
const poEditing = ref<PurchaseOrder | null>(null)
const poForm = ref<Partial<PurchaseOrder>>({ po_type: "corrective", subtotal: 0 })
const savingPO = ref(false)
const poError = ref<string | null>(null)

function openCreatePO() {
  poEditing.value = null
  poForm.value = { po_type: "corrective", subtotal: 0 }
  poError.value = null
  showPOModal.value = true
}

async function openEditPO(row: PurchaseOrder) {
  poEditing.value = row
  poForm.value = { ...await getPO(row.po_no) }
  poError.value = null
  showPOModal.value = true
}

async function savePO() {
  savingPO.value = true
  poError.value = null
  try {
    if (poEditing.value) {
      await updatePO(poEditing.value.po_no, poForm.value as PurchaseOrder)
    } else {
      await createPO(poForm.value as PurchaseOrder)
    }
    await refreshPOs()
    showPOModal.value = false
  } catch (e: unknown) {
    poError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingPO.value = false
  }
}

// ── Invoice Modal ─────────────────────────────────────────────
const showInvoiceModal = ref(false)
const invoiceEditing = ref<Invoice | null>(null)
const invoiceForm = ref<Partial<Invoice>>({ status: "processing", invoice_type: "parts", subtotal: 0, tax_cert: false })
const savingInvoice = ref(false)
const invoiceError = ref<string | null>(null)

function openCreateInvoice() {
  invoiceEditing.value = null
  invoiceForm.value = { status: "processing", invoice_type: "parts", subtotal: 0, tax_cert: false }
  invoiceError.value = null
  showInvoiceModal.value = true
}

async function openEditInvoice(row: Invoice) {
  invoiceEditing.value = row
  invoiceForm.value = { ...await getInvoice(row.id!) }
  invoiceError.value = null
  showInvoiceModal.value = true
}

async function saveInvoice() {
  savingInvoice.value = true
  invoiceError.value = null
  try {
    if (invoiceEditing.value?.id) {
      await updateInvoice(invoiceEditing.value.id, invoiceForm.value as Invoice)
    } else {
      await createInvoice(invoiceForm.value as Invoice)
    }
    await refreshInvoices()
    showInvoiceModal.value = false
  } catch (e: unknown) {
    invoiceError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingInvoice.value = false
  }
}

// ── Budget Modal ──────────────────────────────────────────────
const showBudgetModal = ref(false)
const budgetEditing = ref<Budget | null>(null)
const budgetForm = ref<Partial<Budget>>({})
const savingBudget = ref(false)
const budgetError = ref<string | null>(null)

function openCreateBudget() {
  budgetEditing.value = null
  budgetForm.value = {}
  budgetError.value = null
  showBudgetModal.value = true
}

function openEditBudget(row: Budget) {
  budgetEditing.value = row
  budgetForm.value = { ...row }
  budgetError.value = null
  showBudgetModal.value = true
}

async function saveBudgetEntry() {
  savingBudget.value = true
  budgetError.value = null
  try {
    if (budgetEditing.value?.id) {
      await updateBudget(budgetEditing.value.id, budgetForm.value as Budget)
    } else {
      await createBudget(budgetForm.value as Budget)
    }
    await refreshBudgets()
    showBudgetModal.value = false
  } catch (e: unknown) {
    budgetError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingBudget.value = false
  }
}

// ── Delete modals ─────────────────────────────────────────────
const deletePOTarget = ref<PurchaseOrder | null>(null)
const deletingPO = ref(false)
const showDeletePOModal = computed({ get: () => !!deletePOTarget.value, set: (v) => { if (!v) deletePOTarget.value = null } })

async function confirmDeletePO() {
  if (!deletePOTarget.value) return
  deletingPO.value = true
  try { await removePO(deletePOTarget.value.po_no); await refreshPOs(); deletePOTarget.value = null }
  finally { deletingPO.value = false }
}

const deleteInvoiceTarget = ref<Invoice | null>(null)
const deletingInvoice = ref(false)
const showDeleteInvoiceModal = computed({ get: () => !!deleteInvoiceTarget.value, set: (v) => { if (!v) deleteInvoiceTarget.value = null } })

async function confirmDeleteInvoice() {
  if (!deleteInvoiceTarget.value?.id) return
  deletingInvoice.value = true
  try { await removeInvoice(deleteInvoiceTarget.value.id); await refreshInvoices(); deleteInvoiceTarget.value = null }
  finally { deletingInvoice.value = false }
}

const deleteBudgetTarget = ref<Budget | null>(null)
const deletingBudget = ref(false)
const showDeleteBudgetModal = computed({ get: () => !!deleteBudgetTarget.value, set: (v) => { if (!v) deleteBudgetTarget.value = null } })

async function confirmDeleteBudget() {
  if (!deleteBudgetTarget.value?.id) return
  deletingBudget.value = true
  try { await removeBudget(deleteBudgetTarget.value.id); await refreshBudgets(); deleteBudgetTarget.value = null }
  finally { deletingBudget.value = false }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Finance</h1>
      <div class="flex gap-2">
        <UButton v-if="activeTab === 'pos'" leading-icon="i-heroicons-plus" @click="openCreatePO">New PO</UButton>
        <UButton v-if="activeTab === 'invoices'" leading-icon="i-heroicons-plus" @click="openCreateInvoice">New Invoice</UButton>
        <UButton v-if="activeTab === 'budgets'" leading-icon="i-heroicons-plus" @click="openCreateBudget">New Budget</UButton>
      </div>
    </div>

    <!-- KPIs -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <UCard>
        <div class="flex items-center gap-3">
          <UIcon name="i-heroicons-document-text" class="h-8 w-8 text-blue-500" />
          <div><p class="text-xs text-gray-500">Total PO Value</p><p class="text-xl font-bold">${{ totalPOValue.toLocaleString() }}</p></div>
        </div>
      </UCard>
      <UCard>
        <div class="flex items-center gap-3">
          <UIcon name="i-heroicons-banknotes" class="h-8 w-8 text-green-500" />
          <div><p class="text-xs text-gray-500">Total Invoice Value</p><p class="text-xl font-bold">${{ totalInvoiceValue.toLocaleString() }}</p></div>
        </div>
      </UCard>
      <UCard>
        <div class="flex items-center gap-3">
          <UIcon name="i-heroicons-calculator" class="h-8 w-8 text-purple-500" />
          <div><p class="text-xs text-gray-500">Budget Entries</p><p class="text-xl font-bold">{{ budgets?.length ?? 0 }}</p></div>
        </div>
      </UCard>
    </div>

    <!-- Tabs -->
    <div class="flex gap-2 border-b border-gray-200">
      <button v-for="tab in [{ value: 'pos', label: 'Purchase Orders' }, { value: 'invoices', label: 'Invoices' }, { value: 'budgets', label: 'Budgets' }]" :key="tab.value"
        class="border-b-2 px-4 py-2 text-sm font-medium transition-colors"
        :class="activeTab === tab.value ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
        @click="activeTab = tab.value">
        {{ tab.label }}
      </button>
    </div>

    <UCard>
      <template v-if="activeTab !== 'budgets'" #header>
        <UInput v-model="search" placeholder="Search..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
      </template>

      <UTable v-if="activeTab === 'pos'" :data="filteredPOs" :columns="poColumns">
        <template #subtotal-cell="{ row: { original: row } }">${{ row.subtotal.toLocaleString() }}</template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEditPO(row)" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deletePOTarget = row" />
          </div>
        </template>
      </UTable>

      <UTable v-else-if="activeTab === 'invoices'" :data="filteredInvoices" :columns="invoiceColumns">
        <template #status-cell="{ row: { original: row } }">
          <UBadge :color="invoiceStatusColors[row.status] ?? 'neutral'" variant="soft">{{ row.status }}</UBadge>
        </template>
        <template #subtotal-cell="{ row: { original: row } }">${{ row.subtotal.toLocaleString() }}</template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEditInvoice(row)" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteInvoiceTarget = row" />
          </div>
        </template>
      </UTable>

      <UTable v-else :data="budgets ?? []" :columns="budgetColumns">
        <template #amount-cell="{ row: { original: row } }">${{ row.amount.toLocaleString() }}</template>
        <template #notes-cell="{ row: { original: row } }"><span class="text-slate-500">{{ row.notes ?? "—" }}</span></template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEditBudget(row)" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteBudgetTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- PO Modal -->
    <UModal v-model:open="showPOModal" :ui="{ content: 'max-w-2xl' }">
      <template #content>
        <div class="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-xl bg-white shadow-xl">
          <div class="flex shrink-0 items-center justify-between border-b border-slate-100 px-6 py-5">
            <h3 class="text-base font-semibold text-slate-900">{{ poEditing ? `Edit PO: ${poEditing.po_no}` : "New Purchase Order" }}</h3>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showPOModal = false" />
          </div>
          <div class="flex-1 overflow-y-auto px-6 py-5">
            <div class="grid grid-cols-2 gap-x-5 gap-y-4">
              <UFormField label="PO No" required>
                <UInput v-model="poForm.po_no" placeholder="e.g. PO-2025-001" :disabled="!!poEditing" class="w-full" />
              </UFormField>
              <UFormField label="PO Date">
                <UInput v-model="poForm.po_date" type="date" class="w-full" />
              </UFormField>
              <UFormField label="Supplier">
                <USelect v-model="poForm.supplier_id" :items="supplierOptions" placeholder="Select supplier" class="w-full" />
              </UFormField>
              <UFormField label="Asset">
                <USelect v-model="poForm.asset_id" :items="assetOptions" placeholder="Select asset" class="w-full" />
              </UFormField>
              <UFormField label="Location">
                <USelect v-model="poForm.location_id" :items="locationOptions" placeholder="Select location" class="w-full" />
              </UFormField>
              <UFormField label="PO Type">
                <USelect v-model="poForm.po_type" :items="poTypeOptions" class="w-full" />
              </UFormField>
              <UFormField label="Cost Centre">
                <USelect v-model="poForm.cost_centre_id" :items="costCentreOptions" placeholder="Select cost centre" class="w-full" />
              </UFormField>
              <UFormField label="Subtotal ($)" required>
                <UInput v-model.number="poForm.subtotal" type="number" step="0.01" class="w-full" />
              </UFormField>
              <UFormField label="Description" class="col-span-2">
                <UTextarea v-model="poForm.description" :rows="3" class="w-full" />
              </UFormField>
            </div>
            <UAlert v-if="poError" color="error" variant="soft" :description="poError" class="mt-4" />
          </div>
          <div class="flex shrink-0 justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showPOModal = false">Cancel</UButton>
            <UButton :loading="savingPO" @click="savePO">{{ poEditing ? "Save Changes" : "Create PO" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Invoice Modal -->
    <UModal v-model:open="showInvoiceModal" :ui="{ content: 'max-w-2xl' }">
      <template #content>
        <div class="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-xl bg-white shadow-xl">
          <div class="flex shrink-0 items-center justify-between border-b border-slate-100 px-6 py-5">
            <h3 class="text-base font-semibold text-slate-900">{{ invoiceEditing ? `Edit Invoice #${invoiceEditing.id}` : "New Invoice" }}</h3>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showInvoiceModal = false" />
          </div>
          <div class="flex-1 overflow-y-auto px-6 py-5">
            <div class="grid grid-cols-2 gap-x-5 gap-y-4">
              <UFormField label="Invoice No" required>
                <UInput v-model="invoiceForm.invoice_no" placeholder="e.g. INV-2025-001" class="w-full" />
              </UFormField>
              <UFormField label="Job Date">
                <UInput v-model="invoiceForm.job_date" type="date" class="w-full" />
              </UFormField>
              <UFormField label="Received Date">
                <UInput v-model="invoiceForm.rec_date" type="date" class="w-full" />
              </UFormField>
              <UFormField label="Supplier">
                <USelect v-model="invoiceForm.supplier_id" :items="supplierOptions" placeholder="Select supplier" class="w-full" />
              </UFormField>
              <UFormField label="Asset">
                <USelect v-model="invoiceForm.asset_id" :items="assetOptions" placeholder="Select asset" class="w-full" />
              </UFormField>
              <UFormField label="Location">
                <USelect v-model="invoiceForm.location_id" :items="locationOptions" placeholder="Select location" class="w-full" />
              </UFormField>
              <UFormField label="PO No">
                <UInput v-model="invoiceForm.po_no" placeholder="Linked PO" class="w-full" />
              </UFormField>
              <UFormField label="Work Order ID">
                <UInput v-model.number="invoiceForm.work_order_id" type="number" class="w-full" />
              </UFormField>
              <UFormField label="Invoice Type">
                <USelect v-model="invoiceForm.invoice_type" :items="invoiceTypeOptions" class="w-full" />
              </UFormField>
              <UFormField label="Status">
                <USelect v-model="invoiceForm.status" :items="invoiceStatusOptions" class="w-full" />
              </UFormField>
              <UFormField label="Subtotal ($)" required>
                <UInput v-model.number="invoiceForm.subtotal" type="number" step="0.01" class="w-full" />
              </UFormField>
              <UFormField label="Tax Certificate">
                <UCheckbox v-model="invoiceForm.tax_cert" label="Tax certificate available" />
              </UFormField>
              <UFormField label="Description" class="col-span-2">
                <UTextarea v-model="invoiceForm.description" :rows="3" class="w-full" />
              </UFormField>
            </div>
            <UAlert v-if="invoiceError" color="error" variant="soft" :description="invoiceError" class="mt-4" />
          </div>
          <div class="flex shrink-0 justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showInvoiceModal = false">Cancel</UButton>
            <UButton :loading="savingInvoice" @click="saveInvoice">{{ invoiceEditing ? "Save Changes" : "Create Invoice" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Budget Modal -->
    <UModal v-model:open="showBudgetModal">
      <template #content>
        <div class="flex max-h-[90vh] w-full max-w-lg flex-col rounded-xl bg-white shadow-xl">
          <div class="flex shrink-0 items-center justify-between border-b border-slate-100 px-6 py-5">
            <h3 class="text-base font-semibold text-slate-900">{{ budgetEditing ? "Edit Budget Entry" : "New Budget Entry" }}</h3>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showBudgetModal = false" />
          </div>
          <div class="flex-1 overflow-y-auto px-6 py-5">
            <div class="grid grid-cols-2 gap-x-5 gap-y-4">
              <UFormField label="GL Code" required>
                <UInput v-model="budgetForm.gl_code" placeholder="e.g. 5001" class="w-full" />
              </UFormField>
              <UFormField label="Financial Year" required>
                <UInput v-model="budgetForm.financial_year" placeholder="e.g. 2025/2026" class="w-full" />
              </UFormField>
              <UFormField label="Month" required>
                <USelect v-model="budgetForm.month" :items="monthOptions" placeholder="Select month" class="w-full" />
              </UFormField>
              <UFormField label="Amount ($)" required>
                <UInput v-model.number="budgetForm.amount" type="number" step="0.01" class="w-full" />
              </UFormField>
              <UFormField label="Notes" class="col-span-2">
                <UTextarea v-model="budgetForm.notes" :rows="2" class="w-full" />
              </UFormField>
            </div>
            <UAlert v-if="budgetError" color="error" variant="soft" :description="budgetError" class="mt-4" />
          </div>
          <div class="flex shrink-0 justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showBudgetModal = false">Cancel</UButton>
            <UButton :loading="savingBudget" @click="saveBudgetEntry">{{ budgetEditing ? "Save Changes" : "Create Entry" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete modals -->
    <UModal v-model:open="showDeletePOModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Purchase Order</h3></template>
          <p class="text-sm text-slate-500">Delete PO <strong>{{ deletePOTarget?.po_no }}</strong>? This cannot be undone.</p>
          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton variant="ghost" @click="deletePOTarget = null">Cancel</UButton>
              <UButton color="error" :loading="deletingPO" @click="confirmDeletePO">Delete</UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <UModal v-model:open="showDeleteInvoiceModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Invoice</h3></template>
          <p class="text-sm text-slate-500">Delete invoice <strong>{{ deleteInvoiceTarget?.invoice_no }}</strong>? This cannot be undone.</p>
          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton variant="ghost" @click="deleteInvoiceTarget = null">Cancel</UButton>
              <UButton color="error" :loading="deletingInvoice" @click="confirmDeleteInvoice">Delete</UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <UModal v-model:open="showDeleteBudgetModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Budget Entry</h3></template>
          <p class="text-sm text-slate-500">Delete budget entry for <strong>{{ deleteBudgetTarget?.month }} {{ deleteBudgetTarget?.financial_year }}</strong>? This cannot be undone.</p>
          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton variant="ghost" @click="deleteBudgetTarget = null">Cancel</UButton>
              <UButton color="error" :loading="deletingBudget" @click="confirmDeleteBudget">Delete</UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
  </div>
</template>
