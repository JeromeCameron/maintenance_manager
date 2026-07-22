<script setup lang="ts">
import type { PurchaseOrder, Invoice, Budget } from "~/types"

const { isAdmin } = useAuth()
const { getPOs, getPO, createPO, updatePO, removePO, getInvoices, getInvoice, createInvoice, updateInvoice, removeInvoice, getBudgets, createBudget, updateBudget, removeBudget, getCostCentres } = useFinance()
const { getAll: getAssets } = useAssets()
const { getAll: getSuppliers } = useSuppliers()
const { getAll: getLocations } = useLocations()
const { getAll: getWorkOrders } = useWorkOrders()

const [{ data: pos, refresh: refreshPOs }, { data: invoices, refresh: refreshInvoices }, { data: budgets, refresh: refreshBudgets }, { data: assets }, { data: suppliers }, { data: locations }, { data: costCentres }, { data: workOrders }] = await Promise.all([
  useAsyncData("pos", () => getPOs()),
  useAsyncData("invoices", () => getInvoices()),
  useAsyncData("budgets", () => getBudgets()),
  useAsyncData("assets-select", () => getAssets()),
  useAsyncData("suppliers-select", () => getSuppliers()),
  useAsyncData("locations-select", () => getLocations()),
  useAsyncData("cost-centres", () => getCostCentres()),
  useAsyncData("finance-work-orders", () => getWorkOrders()),
])

const activeTab = ref("pos")

const invoiceStatusColors: Record<string, string> = { processing: "info", submitted: "success", on_hold: "warning" }

const poTypeStyles: Record<string, string> = {
  corrective:   "bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400",
  predictive:   "bg-purple-50 text-purple-600 dark:bg-purple-500/10 dark:text-purple-400",
  preventative: "bg-teal-50 text-teal-700 dark:bg-teal-500/10 dark:text-teal-400",
  consumables:  "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400",
  rental:       "bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-400",
}

const invoiceTypeStyles: Record<string, string> = {
  parts:             "bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400",
  parts_and_labour:  "bg-violet-50 text-violet-600 dark:bg-violet-500/10 dark:text-violet-400",
  labour:            "bg-orange-50 text-orange-600 dark:bg-orange-500/10 dark:text-orange-400",
  consumables:       "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400",
  services:          "bg-sky-50 text-sky-600 dark:bg-sky-500/10 dark:text-sky-400",
}

const _MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

function fmtDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—"
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return "—"
  return `${String(d.getUTCDate()).padStart(2,"0")}-${_MONTHS[d.getUTCMonth()]}-${String(d.getUTCFullYear()).slice(-2)}`
}

const search = ref("")

// ── PO balances (subtotal minus all linked invoices) ───────────
const poInvoicedMap = computed(() => {
  const m: Record<string, number> = {}
  for (const i of invoices.value ?? []) { if (i.po_no) m[i.po_no] = (m[i.po_no] ?? 0) + i.subtotal }
  return m
})
function poBalanceFor(po: PurchaseOrder): number {
  return po.subtotal - (poInvoicedMap.value[po.po_no] ?? 0)
}

const showOutstandingPOsOnly = ref(false)
const filteredPOs = computed(() =>
  (pos.value ?? [])
    .filter((p) => !search.value || p.po_no.toLowerCase().includes(search.value.toLowerCase()) || (p.description ?? "").toLowerCase().includes(search.value.toLowerCase()))
    .filter((p) => !showOutstandingPOsOnly.value || poBalanceFor(p) > 0)
    .sort((a, b) => (b.po_date ?? "").localeCompare(a.po_date ?? ""))
)
const filteredInvoices = computed(() =>
  (invoices.value ?? [])
    .filter((i) => !search.value || i.invoice_no.toLowerCase().includes(search.value.toLowerCase()) || (i.description ?? "").toLowerCase().includes(search.value.toLowerCase()))
    .sort((a, b) => (b.invoice_date ?? "").localeCompare(a.invoice_date ?? ""))
)
// ── Shared options ────────────────────────────────────────────
const assetOptions = computed(() => (assets.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id })))
const supplierOptions = computed(() => (suppliers.value ?? []).map((s) => ({ label: s.name, value: s.supplier_id })))
const locationOptions = computed(() => (locations.value ?? []).map((l) => ({ label: l.name, value: l.location_id })))
const poOptions = computed(() => [
  { label: "— None —", value: null },
  ...[...(pos.value ?? [])].sort((a, b) => a.po_no.localeCompare(b.po_no)).map((p) => ({ label: `${p.po_no}${p.description ? ` — ${p.description}` : ""}`, value: p.po_no })),
])
const workOrderOptions = computed(() => [
  { label: "— None —", value: null },
  ...[...(workOrders.value ?? [])].sort((a, b) => (a.work_order_id ?? 0) - (b.work_order_id ?? 0)).map((w) => ({ label: `WO-${w.work_order_id}${w.description ? ` — ${w.description}` : ""}`, value: w.work_order_id })),
])
const costCentreOptions = computed(() => (costCentres.value ?? []).map((c) => ({ label: `${c.gl_code}${c.description ? ` — ${c.description}` : ""}`, value: c.gl_code })))
const poTypeOptions = ["corrective", "predictive", "preventative", "consumables", "rental"]
const invoiceStatusOptions = ["processing", "submitted", "on_hold"]
const invoiceTypeOptions = ["parts", "parts_and_labour", "labour", "consumables", "services"]
function monthToFY(yyyyMm: string): string {
  const [year, month] = yyyyMm.split("-").map(Number)
  const fyEnd = month >= 4 ? year + 1 : year
  return `FY${String(fyEnd).slice(-2)}`
}

// ── PO Modal ──────────────────────────────────────────────────
const showPOModal = ref(false)
const poEditing = ref<PurchaseOrder | null>(null)
const poForm = ref<Partial<PurchaseOrder>>({ po_type: "corrective", subtotal: 0 })
const savingPO = ref(false)
const poError = ref<string | null>(null)
const poModalTab = ref<"details" | "invoices">("details")

const poRelatedInvoices = computed(() =>
  poEditing.value
    ? (invoices.value ?? []).filter((i) => i.po_no === poEditing.value!.po_no)
    : []
)
const poInvoicedTotal = computed(() => poRelatedInvoices.value.reduce((s, i) => s + i.subtotal, 0))
const poBalance = computed(() => (poForm.value.subtotal ?? 0) - poInvoicedTotal.value)

function openCreatePO() {
  poEditing.value = null
  poForm.value = { po_type: "corrective", subtotal: 0 }
  poError.value = null
  poModalTab.value = "details"
  showPOModal.value = true
}

async function openEditPO(row: PurchaseOrder) {
  poEditing.value = row
  poForm.value = { ...await getPO(row.po_no) }
  poError.value = null
  poModalTab.value = "details"
  showPOModal.value = true
}

function openInvoiceFromPO(inv: Invoice) {
  showPOModal.value = false
  openEditInvoice(inv)
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
  budgetForm.value = { ...row, month: row.month ? String(row.month).slice(0, 7) : undefined }
  budgetError.value = null
  showBudgetModal.value = true
}

async function saveBudgetEntry() {
  savingBudget.value = true
  budgetError.value = null
  try {
    const payload = { ...budgetForm.value }
    if (payload.month && /^\d{4}-\d{2}$/.test(String(payload.month))) {
      payload.financial_year = monthToFY(String(payload.month))
      payload.month = `${payload.month}-01` as any
    }
    if (budgetEditing.value?.id) {
      await updateBudget(budgetEditing.value.id, payload as Budget)
    } else {
      await createBudget(payload as Budget)
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
    <!-- Tabs -->
    <div class="flex gap-2 border-b border-gray-200 dark:border-slate-700">
      <button v-for="tab in [{ value: 'pos', label: 'Purchase Orders' }, { value: 'invoices', label: 'Invoices' }, { value: 'budgets', label: 'Budgets' }]" :key="tab.value"
        class="border-b-2 px-4 py-2 text-sm font-medium transition-colors"
        :class="activeTab === tab.value ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-300'"
        @click="activeTab = tab.value">
        {{ tab.label }}
      </button>
    </div>

    <UCard>
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <div class="flex flex-wrap items-center gap-3">
            <UInput v-if="activeTab !== 'budgets'" v-model="search" placeholder="Search..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
            <label v-if="activeTab === 'pos'" class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300 select-none">
              <UCheckbox v-model="showOutstandingPOsOnly" />
              Open PO's
            </label>
          </div>
          <div class="flex gap-2">
            <UButton v-if="activeTab === 'pos'" leading-icon="i-heroicons-plus" @click="openCreatePO" class="!bg-blue-700 hover:!bg-blue-800">New PO</UButton>
            <UButton v-if="activeTab === 'invoices'" leading-icon="i-heroicons-plus" @click="openCreateInvoice" class="!bg-blue-700 hover:!bg-blue-800">New Invoice</UButton>
            <UButton v-if="activeTab === 'budgets'" leading-icon="i-heroicons-plus" @click="openCreateBudget" class="!bg-blue-700 hover:!bg-blue-800">New Budget</UButton>
          </div>
        </div>
      </template>

      <!-- Purchase Orders card list -->
      <div v-if="activeTab === 'pos'" class="space-y-2">
        <div v-if="filteredPOs.length === 0" class="py-12 text-center text-sm text-gray-400 dark:text-slate-500">
          No purchase orders found.
        </div>
        <div
          v-for="po in filteredPOs"
          :key="po.po_no"
          class="flex cursor-pointer items-start gap-4 rounded-lg px-5 py-4 ring-1 ring-gray-200 dark:ring-slate-700 hover:bg-blue-50/40 dark:hover:bg-blue-500/10 transition-colors border-l-4 border-l-transparent"
          @click="openEditPO(po)"
        >
          <div class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gray-100 dark:bg-slate-800">
            <UIcon name="i-heroicons-document-text" class="h-4 w-4 text-gray-400 dark:text-slate-500" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <span class="text-sm font-semibold text-slate-800 dark:text-slate-100">{{ po.po_no }}</span>
            </div>
            <p class="mt-0.5 truncate text-xs text-gray-500 dark:text-slate-400" :title="po.description ?? ''">{{ po.description ?? "—" }}</p>
            <div class="mt-1.5 flex flex-wrap items-center gap-2">
              <span
                v-if="po.po_type"
                class="inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium capitalize"
                :class="poTypeStyles[po.po_type] ?? 'bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400'"
              >{{ po.po_type }}</span>
              <span v-if="po.po_date" class="flex items-center gap-1 text-[11px] text-gray-400 dark:text-slate-500">
                <UIcon name="i-heroicons-calendar" class="h-3 w-3" />
                {{ fmtDate(po.po_date) }}
              </span>
            </div>
          </div>
          <div class="shrink-0 flex flex-col items-end gap-1">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-300">${{ po.subtotal.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</span>
            <span class="text-[11px] font-medium" :class="poBalanceFor(po) > 0 ? 'text-amber-600' : 'text-gray-400 dark:text-slate-500'">
              Balance: ${{ poBalanceFor(po).toLocaleString('en-US', { minimumFractionDigits: 2 }) }}
            </span>
            <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click.stop="deletePOTarget = po" />
          </div>
        </div>
      </div>

      <!-- Invoices card list -->
      <div v-else-if="activeTab === 'invoices'" class="space-y-2">
        <div v-if="filteredInvoices.length === 0" class="py-12 text-center text-sm text-gray-400 dark:text-slate-500">
          No invoices found.
        </div>
        <div
          v-for="inv in filteredInvoices"
          :key="inv.id"
          class="flex cursor-pointer items-start gap-4 rounded-lg px-5 py-4 ring-1 ring-gray-200 dark:ring-slate-700 hover:bg-blue-50/40 dark:hover:bg-blue-500/10 transition-colors border-l-4 border-l-transparent"
          @click="openEditInvoice(inv)"
        >
          <div class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gray-100 dark:bg-slate-800">
            <UIcon name="i-heroicons-banknotes" class="h-4 w-4 text-gray-400 dark:text-slate-500" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <span class="text-sm font-semibold text-slate-800 dark:text-slate-100">{{ inv.invoice_no }}</span>
            </div>
            <p class="mt-0.5 truncate text-xs text-gray-500 dark:text-slate-400" :title="inv.description ?? ''">{{ inv.description ?? "—" }}</p>
            <div class="mt-1.5 flex flex-wrap items-center gap-2">
              <span
                v-if="inv.invoice_type"
                class="inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium capitalize"
                :class="invoiceTypeStyles[inv.invoice_type] ?? 'bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400'"
              >{{ inv.invoice_type.replace(/_/g, " ") }}</span>
              <span v-if="inv.invoice_date" class="flex items-center gap-1 text-[11px] text-gray-400 dark:text-slate-500">
                <UIcon name="i-heroicons-calendar" class="h-3 w-3" />
                {{ fmtDate(inv.invoice_date) }}
              </span>
            </div>
          </div>
          <div class="shrink-0 flex flex-col items-end gap-2">
            <UBadge :color="invoiceStatusColors[inv.status] ?? 'neutral'" variant="soft" size="xs" class="capitalize">{{ inv.status }}</UBadge>
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-300">${{ inv.subtotal.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</span>
            <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click.stop="deleteInvoiceTarget = inv" />
          </div>
        </div>
      </div>

      <!-- Budgets card list -->
      <div v-else class="space-y-2">
        <div v-if="(budgets ?? []).length === 0" class="py-12 text-center text-sm text-gray-400 dark:text-slate-500">
          No budget entries found.
        </div>
        <div
          v-for="b in budgets ?? []"
          :key="b.id"
          class="flex cursor-pointer items-start gap-4 rounded-lg px-5 py-4 ring-1 ring-gray-200 dark:ring-slate-700 hover:bg-blue-50/40 dark:hover:bg-blue-500/10 transition-colors border-l-4 border-l-transparent"
          @click="openEditBudget(b)"
        >
          <div class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gray-100 dark:bg-slate-800">
            <UIcon name="i-heroicons-chart-pie" class="h-4 w-4 text-gray-400 dark:text-slate-500" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <span class="text-sm font-semibold text-slate-800 dark:text-slate-100">{{ b.gl_code }}</span>
              <span class="text-xs text-slate-400 dark:text-slate-500">· {{ b.financial_year }}</span>
            </div>
            <p class="mt-0.5 truncate text-xs text-gray-500 dark:text-slate-400">{{ b.notes ?? "—" }}</p>
            <div class="mt-1.5 flex flex-wrap items-center gap-2">
              <span class="flex items-center gap-1 text-[11px] text-gray-400 dark:text-slate-500">
                <UIcon name="i-heroicons-calendar" class="h-3 w-3" />
                {{ fmtDate(b.month) }}
              </span>
            </div>
          </div>
          <div class="shrink-0 flex flex-col items-end gap-2">
            <span class="text-sm font-semibold text-slate-700 dark:text-slate-300">${{ b.amount.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</span>
            <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click.stop="deleteBudgetTarget = b" />
          </div>
        </div>
      </div>
    </UCard>

    <!-- PO Modal -->
    <UModal v-model:open="showPOModal" :ui="{ content: 'max-w-2xl' }">
      <template #content>
        <div class="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-xl bg-white dark:bg-slate-900 shadow-xl">
          <div class="flex shrink-0 items-center gap-3 border-b border-slate-100 dark:border-slate-800 px-6 py-5">
            <div class="flex-1 min-w-0">
              <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100 truncate">{{ poEditing ? `Edit PO: ${poEditing.po_no}` : "New Purchase Order" }}</h3>
            </div>
            <span
              v-if="poEditing"
              class="rounded-lg px-3 py-1 text-sm font-bold tracking-wide shrink-0"
              :class="poBalance < 0 ? 'bg-red-600 text-white' : 'bg-slate-800 text-white'"
            >
              Balance: ${{ poBalance.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}
            </span>
            <div class="flex-1 flex justify-end">
              <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showPOModal = false" />
            </div>
          </div>

          <!-- Tab bar (edit mode only) -->
          <div v-if="poEditing" class="flex shrink-0 gap-0 border-b border-gray-200 dark:border-slate-700 px-6">
            <button
              v-for="tab in [{ value: 'details', label: 'Details' }, { value: 'invoices', label: `Invoices (${poRelatedInvoices.length})` }]"
              :key="tab.value"
              class="border-b-2 px-4 py-3 text-sm font-medium transition-colors"
              :class="poModalTab === tab.value ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-300'"
              @click="poModalTab = tab.value as 'details' | 'invoices'"
            >{{ tab.label }}</button>
          </div>

          <div class="flex-1 overflow-y-auto px-6 py-5">
            <!-- Details tab -->
            <template v-if="!poEditing || poModalTab === 'details'">
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
                <UFormField label="Subtotal" required>
                  <UInput v-model.number="poForm.subtotal" type="number" step="0.01" class="w-full">
                    <template #leading><span class="text-slate-400 dark:text-slate-500 text-sm select-none">$</span></template>
                  </UInput>
                </UFormField>
                <UFormField label="Description" class="col-span-2">
                  <UTextarea v-model="poForm.description" :rows="3" class="w-full" />
                </UFormField>
              </div>
              <UAlert v-if="poError" color="error" variant="soft" :description="poError" class="mt-4" />
            </template>

            <!-- Invoices tab -->
            <template v-else-if="poModalTab === 'invoices'">
              <div class="mb-4 flex items-center gap-4 rounded-lg bg-slate-50 dark:bg-slate-800 px-4 py-3">
                <div>
                  <p class="text-xs text-slate-400 dark:text-slate-500">PO Value</p>
                  <p class="text-sm font-semibold text-slate-800 dark:text-slate-100">${{ (poForm.subtotal ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</p>
                </div>
                <div>
                  <p class="text-xs text-slate-400 dark:text-slate-500">Invoiced</p>
                  <p class="text-sm font-semibold text-slate-800 dark:text-slate-100">${{ poInvoicedTotal.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</p>
                </div>
                <div>
                  <p class="text-xs text-slate-400 dark:text-slate-500">Balance</p>
                  <p class="text-sm font-semibold" :class="poBalance < 0 ? 'text-red-600' : 'text-slate-800 dark:text-slate-100'">
                    ${{ poBalance.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}
                  </p>
                </div>
              </div>

              <div v-if="poRelatedInvoices.length === 0" class="py-10 text-center text-sm text-slate-400 dark:text-slate-500">
                No invoices linked to this PO yet.
              </div>
              <div v-else class="space-y-2">
                <div
                  v-for="inv in poRelatedInvoices"
                  :key="inv.id"
                  class="flex cursor-pointer items-start gap-4 rounded-lg px-4 py-3 ring-1 ring-gray-200 dark:ring-slate-700 hover:bg-blue-50/40 dark:hover:bg-blue-500/10 transition-colors"
                  @click="openInvoiceFromPO(inv)"
                >
                  <div class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-100 dark:bg-slate-800">
                    <UIcon name="i-heroicons-banknotes" class="h-4 w-4 text-gray-400 dark:text-slate-500" />
                  </div>
                  <div class="min-w-0 flex-1">
                    <span class="text-sm font-semibold text-slate-800 dark:text-slate-100">{{ inv.invoice_no }}</span>
                    <p class="mt-0.5 truncate text-xs text-gray-500 dark:text-slate-400" :title="inv.description ?? ''">{{ inv.description ?? "—" }}</p>
                    <div class="mt-1.5 flex flex-wrap items-center gap-2">
                      <span
                        v-if="inv.invoice_type"
                        class="inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium capitalize"
                        :class="invoiceTypeStyles[inv.invoice_type] ?? 'bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400'"
                      >{{ inv.invoice_type.replace(/_/g, " ") }}</span>
                      <span v-if="inv.invoice_date" class="flex items-center gap-1 text-[11px] text-gray-400 dark:text-slate-500">
                        <UIcon name="i-heroicons-calendar" class="h-3 w-3" />
                        {{ fmtDate(inv.invoice_date) }}
                      </span>
                    </div>
                  </div>
                  <div class="shrink-0 flex flex-col items-end gap-2">
                    <UBadge :color="invoiceStatusColors[inv.status] ?? 'neutral'" variant="soft" size="xs" class="capitalize">{{ inv.status }}</UBadge>
                    <span class="text-sm font-semibold text-slate-700 dark:text-slate-300">${{ inv.subtotal.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</span>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <div class="flex shrink-0 justify-end gap-3 border-t border-slate-100 dark:border-slate-800 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showPOModal = false">Cancel</UButton>
            <UButton v-if="!poEditing || poModalTab === 'details'" :loading="savingPO" @click="savePO">{{ poEditing ? "Save Changes" : "Create PO" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Invoice Modal -->
    <UModal v-model:open="showInvoiceModal" :ui="{ content: 'max-w-2xl' }">
      <template #content>
        <div class="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-xl bg-white dark:bg-slate-900 shadow-xl">
          <div class="flex shrink-0 items-center justify-between border-b border-slate-100 dark:border-slate-800 px-6 py-5">
            <div class="flex items-center gap-3 min-w-0">
              <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100 shrink-0">{{ invoiceEditing ? `Edit Invoice #${invoiceEditing.id}` : "New Invoice" }}</h3>
              <UBadge
                :color="invoiceStatusColors[invoiceForm.status ?? ''] ?? 'neutral'"
                variant="solid"
                size="md"
                class="capitalize shrink-0"
              >{{ (invoiceForm.status ?? 'processing').replace('_', ' ') }}</UBadge>
              <span class="rounded-lg bg-slate-800 px-3 py-1 text-sm font-bold text-white tracking-wide shrink-0">
                ${{ (invoiceForm.subtotal ?? 0).toLocaleString('en-US', { minimumFractionDigits: 2 }) }}
              </span>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showInvoiceModal = false" />
          </div>
          <div class="flex-1 overflow-y-auto px-6 py-5">
            <div class="grid grid-cols-2 gap-x-5 gap-y-4">
              <UFormField label="Invoice No" required>
                <UInput v-model="invoiceForm.invoice_no" placeholder="e.g. INV-2025-001" class="w-full" />
              </UFormField>
              <UFormField label="Invoice Date">
                <UInput v-model="invoiceForm.invoice_date" type="date" class="w-full" />
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
                <USelect v-model="invoiceForm.po_no" :items="poOptions" placeholder="Select PO" searchable searchable-placeholder="Type PO number…" class="w-full" />
              </UFormField>
              <UFormField label="Work Order ID">
                <USelect v-model="invoiceForm.work_order_id" :items="workOrderOptions" placeholder="Select work order" searchable searchable-placeholder="Type WO number…" class="w-full" />
              </UFormField>
              <UFormField label="Invoice Type">
                <USelect v-model="invoiceForm.invoice_type" :items="invoiceTypeOptions" class="w-full" />
              </UFormField>
              <UFormField label="Status">
                <USelect v-model="invoiceForm.status" :items="invoiceStatusOptions" class="w-full" />
              </UFormField>
              <UFormField label="Subtotal" required>
                <UInput v-model.number="invoiceForm.subtotal" type="number" step="0.01" class="w-full">
                  <template #leading><span class="text-slate-400 dark:text-slate-500 text-sm select-none">$</span></template>
                </UInput>
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
          <div class="flex shrink-0 justify-end gap-3 border-t border-slate-100 dark:border-slate-800 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showInvoiceModal = false">Cancel</UButton>
            <UButton :loading="savingInvoice" @click="saveInvoice">{{ invoiceEditing ? "Save Changes" : "Create Invoice" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Budget Modal -->
    <UModal v-model:open="showBudgetModal">
      <template #content>
        <div class="flex max-h-[90vh] w-full max-w-lg flex-col rounded-xl bg-white dark:bg-slate-900 shadow-xl">
          <div class="flex shrink-0 items-center justify-between border-b border-slate-100 dark:border-slate-800 px-6 py-5">
            <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">{{ budgetEditing ? "Edit Budget Entry" : "New Budget Entry" }}</h3>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showBudgetModal = false" />
          </div>
          <div class="flex-1 overflow-y-auto px-6 py-5">
            <div class="grid grid-cols-2 gap-x-5 gap-y-4">
              <UFormField label="GL Code" required>
                <USelect v-model="budgetForm.gl_code" :items="costCentreOptions" placeholder="Select GL code" class="w-full" />
              </UFormField>
              <UFormField label="Financial Year">
                <UInput :model-value="budgetForm.month && /^\d{4}-\d{2}$/.test(String(budgetForm.month)) ? monthToFY(String(budgetForm.month)) : (budgetForm.financial_year ?? '')" disabled class="w-full" />
              </UFormField>
              <UFormField label="Month" required>
                <UInput v-model="budgetForm.month" type="month" class="w-full" />
              </UFormField>
              <UFormField label="Amount" required>
                <UInput v-model.number="budgetForm.amount" type="number" step="0.01" class="w-full">
                  <template #leading><span class="text-slate-400 dark:text-slate-500 text-sm select-none">$</span></template>
                </UInput>
              </UFormField>
              <UFormField label="Notes" class="col-span-2">
                <UTextarea v-model="budgetForm.notes" :rows="2" class="w-full" />
              </UFormField>
            </div>
            <UAlert v-if="budgetError" color="error" variant="soft" :description="budgetError" class="mt-4" />
          </div>
          <div class="flex shrink-0 justify-end gap-3 border-t border-slate-100 dark:border-slate-800 px-6 py-4">
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
          <p class="text-sm text-slate-500 dark:text-slate-400">Delete PO <strong>{{ deletePOTarget?.po_no }}</strong>? This cannot be undone.</p>
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
          <p class="text-sm text-slate-500 dark:text-slate-400">Delete invoice <strong>{{ deleteInvoiceTarget?.invoice_no }}</strong>? This cannot be undone.</p>
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
          <p class="text-sm text-slate-500 dark:text-slate-400">Delete budget entry for <strong>{{ deleteBudgetTarget?.month }} {{ deleteBudgetTarget?.financial_year }}</strong>? This cannot be undone.</p>
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
