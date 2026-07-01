<script setup lang="ts">
import type { Supplier, WorkOrder, Invoice, PurchaseOrder } from "~/types"

const { isAdmin } = useAuth()
const { getAll, getOne, create, update, remove } = useSuppliers()
const { getBySupplier: getWOsBySupplier } = useWorkOrders()
const { getInvoicesBySupplier, getPOsBySupplier } = useFinance()

const { data: suppliers, refresh } = await useAsyncData("suppliers", () => getAll())

const columns = [
  { accessorKey: "supplier_id", header: "ID" },
  { accessorKey: "name", header: "Name" },
  { accessorKey: "contact_number", header: "Contact #" },
  { id: "categories", header: "Categories" },
  { id: "actions", header: "" },
]

const CATEGORY_OPTIONS = [
  { label: "Parts", value: "parts" },
  { label: "Services", value: "services" },
  { label: "Rental", value: "rental" },
  { label: "Safety Gears", value: "safety_gears" },
]

const search = ref("")
const filtered = computed(() =>
  (suppliers.value ?? [])
    .filter((s) => {
      const q = search.value.toLowerCase()
      return !q || s.name.toLowerCase().includes(q) || (s.contact_number ?? "").toLowerCase().includes(q)
    })
    .sort((a, b) => a.name.localeCompare(b.name))
)

// ── Form modal ───────────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)

const defaultForm = (): Partial<Supplier> => ({ categories: [] })
const form = ref<Partial<Supplier>>(defaultForm())

function toggleCategory(value: string) {
  const cats = form.value.categories ?? []
  form.value.categories = cats.includes(value)
    ? cats.filter((c) => c !== value)
    : [...cats, value]
}

// ── Related records ──────────────────────────────────────────
const PAGE_SIZE = 15
const activeRelatedTab = ref("details")
const relatedLoading = ref(false)
const relatedWorkOrders = ref<WorkOrder[]>([])
const relatedInvoices = ref<Invoice[]>([])
const relatedPOs = ref<PurchaseOrder[]>([])
const woVisible = ref(PAGE_SIZE)
const invVisible = ref(PAGE_SIZE)
const poVisible = ref(PAGE_SIZE)

const sortedWOs = computed(() =>
  [...relatedWorkOrders.value].sort((a, b) => (b.issue_date ?? "").localeCompare(a.issue_date ?? ""))
)
const sortedInvoices = computed(() =>
  [...relatedInvoices.value].sort((a, b) => (b.invoice_date ?? "").localeCompare(a.invoice_date ?? ""))
)
const sortedPOs = computed(() =>
  [...relatedPOs.value].sort((a, b) => (b.po_date ?? "").localeCompare(a.po_date ?? ""))
)
const visibleWOs = computed(() => sortedWOs.value.slice(0, woVisible.value))
const visibleInvoices = computed(() => sortedInvoices.value.slice(0, invVisible.value))
const visiblePOs = computed(() => sortedPOs.value.slice(0, poVisible.value))

const woColumns = [
  { accessorKey: "work_order_id", header: "WO #" },
  { accessorKey: "issue_date", header: "Issued" },
  { id: "wo-description", header: "Description" },
  { accessorKey: "status", header: "Status" },
  { accessorKey: "asset_id", header: "Asset" },
  { id: "wo-actions", header: "" },
]
const invoiceColumns = [
  { accessorKey: "invoice_no", header: "Invoice No" },
  { accessorKey: "invoice_date", header: "Date" },
  { id: "inv-description", header: "Description" },
  { accessorKey: "invoice_type", header: "Type" },
  { accessorKey: "status", header: "Status" },
  { accessorKey: "subtotal", header: "Subtotal" },
  { id: "inv-actions", header: "" },
]
const poColumns = [
  { accessorKey: "po_no", header: "PO No" },
  { accessorKey: "po_date", header: "Date" },
  { id: "po-description", header: "Description" },
  { accessorKey: "po_type", header: "Type" },
  { accessorKey: "subtotal", header: "Subtotal" },
  { id: "po-actions", header: "" },
]

const woStatusColors: Record<string, string> = {
  requested: "info", scheduled: "info", awaiting_parts: "warning", awaiting_po: "warning",
  in_progress: "warning", on_hold: "neutral", cancelled: "error", completed: "success", closed: "neutral",
}
const invoiceStatusColors: Record<string, string> = { processing: "info", submitted: "success", on_hold: "warning" }

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
function fmtDate(value: string | null | undefined): string {
  if (!value) return "—"
  const [year, month, day] = value.slice(0, 10).split("-").map(Number)
  if (!year || !month || !day) return "—"
  return `${String(day).padStart(2, "0")}-${MONTHS[month - 1]}-${String(year).slice(-2)}`
}

function openCreate() {
  form.value = defaultForm()
  isEditing.value = false
  editId.value = null
  formError.value = null
  relatedWorkOrders.value = []
  relatedInvoices.value = []
  relatedPOs.value = []
  showModal.value = true
}

async function openEdit(id: number) {
  form.value = { ...await getOne(id) }
  isEditing.value = true
  editId.value = id
  formError.value = null
  activeRelatedTab.value = "details"
  woVisible.value = PAGE_SIZE
  invVisible.value = PAGE_SIZE
  poVisible.value = PAGE_SIZE
  showModal.value = true

  relatedLoading.value = true
  try {
    const [wos, invs, pos] = await Promise.all([
      getWOsBySupplier(id).catch(() => [] as WorkOrder[]),
      getInvoicesBySupplier(id).catch(() => [] as Invoice[]),
      getPOsBySupplier(id).catch(() => [] as PurchaseOrder[]),
    ])
    relatedWorkOrders.value = wos
    relatedInvoices.value = invs
    relatedPOs.value = pos
  } finally {
    relatedLoading.value = false
  }
}

async function save() {
  saving.value = true
  formError.value = null
  try {
    if (isEditing.value && editId.value) {
      await update(editId.value, form.value as Supplier)
    } else {
      await create(form.value as Supplier)
    }
    await refresh()
    showModal.value = false
  } catch (e: unknown) {
    formError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    saving.value = false
  }
}

// ── Delete modal ─────────────────────────────────────────────
const deleteTarget = ref<Supplier | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value?.supplier_id) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.supplier_id)
    await refresh()
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <UCard>
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <UInput v-model="search" placeholder="Search by name or contact number..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
          <UButton leading-icon="i-heroicons-plus" @click="openCreate" class="!bg-blue-700 hover:!bg-blue-800">New Supplier</UButton>
        </div>
      </template>
      <UTable :data="filtered" :columns="columns" :ui="{ root: 'relative overflow-auto max-h-[calc(100vh-22rem)]', th: 'bg-slate-100 text-slate-500 font-semibold', tr: 'odd:bg-white even:bg-slate-50 hover:bg-blue-50 transition-colors' }">
        <template #categories-cell="{ row: { original: row } }">
          <div v-if="row.categories?.length" class="flex flex-wrap gap-1">
            <UBadge v-for="cat in row.categories" :key="cat" variant="soft" color="primary" class="capitalize">
              {{ cat.replace(/_/g, " ") }}
            </UBadge>
          </div>
          <span v-else class="text-gray-400">—</span>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-eye" @click="openEdit(row.supplier_id)" />
            <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Create / Edit Modal -->
    <UModal v-model:open="showModal" :ui="{ content: 'max-w-4xl' }">
      <template #content>
        <div class="flex max-h-[90vh] w-full max-w-4xl flex-col rounded-xl bg-white shadow-xl">
          <!-- Header -->
          <div class="flex shrink-0 items-start gap-4 border-b border-gray-100 px-6 py-5">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50">
              <UIcon name="i-heroicons-building-storefront" class="h-5 w-5 text-blue-600" />
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="text-base font-semibold text-slate-900">{{ isEditing ? "Edit Supplier" : "New Supplier" }}</h3>
              <p class="mt-0.5 text-sm text-gray-500">{{ isEditing ? "Update supplier details" : "Add a new supplier" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>

          <!-- Tab bar (edit mode only) -->
          <div v-if="isEditing" class="flex shrink-0 gap-0 border-b border-gray-200 px-6">
            <button
              v-for="tab in [
                { value: 'details', label: 'Details' },
                { value: 'work-orders', label: 'Work Orders', count: sortedWOs.length },
                { value: 'invoices', label: 'Invoices', count: sortedInvoices.length },
                { value: 'purchase-orders', label: 'Purchase Orders', count: sortedPOs.length },
              ]"
              :key="tab.value"
              class="flex items-center gap-1.5 border-b-2 px-4 py-3 text-sm font-medium transition-colors"
              :class="activeRelatedTab === tab.value ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
              @click="activeRelatedTab = tab.value"
            >
              {{ tab.label }}
              <span v-if="tab.count !== undefined" class="rounded-full bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">
                {{ relatedLoading ? "…" : tab.count }}
              </span>
            </button>
          </div>

          <!-- Scrollable body -->
          <div class="flex-1 overflow-y-auto px-6 py-5 space-y-4">

            <!-- Details tab (always shown when creating; shown when activeRelatedTab === 'details' when editing) -->
            <template v-if="!isEditing || activeRelatedTab === 'details'">
              <div class="grid grid-cols-2 gap-x-5 gap-y-4">
                <UFormField label="Name" required class="col-span-2">
                  <UInput v-model="form.name" placeholder="Supplier company name" class="w-full" />
                </UFormField>
                <UFormField label="Primary Contact" required>
                  <UInput v-model="form.primary_contact" placeholder="Contact person name" class="w-full" />
                </UFormField>
                <UFormField label="Contact Title">
                  <UInput v-model="form.contact_title" placeholder="e.g. Account Manager" class="w-full" />
                </UFormField>
                <UFormField label="Contact Number">
                  <UInput v-model="form.contact_number" placeholder="e.g. +61 4xx xxx xxx" class="w-full" />
                </UFormField>
                <UFormField label="Email" required>
                  <UInput v-model="form.email" type="email" class="w-full" />
                </UFormField>
                <UFormField label="Address" required class="col-span-2">
                  <UTextarea v-model="form.address" :rows="3" class="w-full" />
                </UFormField>
                <UFormField label="Notes" class="col-span-2">
                  <UTextarea v-model="form.notes" :rows="3" placeholder="Additional notes…" class="w-full" />
                </UFormField>
                <UFormField label="Categories" class="col-span-2">
                  <div class="flex flex-wrap gap-3 pt-1">
                    <label
                      v-for="opt in CATEGORY_OPTIONS"
                      :key="opt.value"
                      class="flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors"
                      :class="form.categories?.includes(opt.value)
                        ? 'border-primary-500 bg-primary-50 text-primary-700'
                        : 'border-gray-200 text-gray-600 hover:border-gray-300'"
                      @click="toggleCategory(opt.value)"
                    >
                      <UIcon :name="form.categories?.includes(opt.value) ? 'i-heroicons-check-circle' : 'i-heroicons-circle'" class="h-4 w-4" />
                      {{ opt.label }}
                    </label>
                  </div>
                </UFormField>
              </div>
              <UAlert v-if="formError" color="error" variant="soft" :description="formError" />
            </template>

            <!-- Work Orders tab -->
            <template v-else-if="activeRelatedTab === 'work-orders'">
              <div v-if="relatedLoading" class="flex items-center justify-center py-8 text-sm text-slate-400">Loading…</div>
              <template v-else>
                <UTable
                  :data="visibleWOs"
                  :columns="woColumns"
                  :ui="{ th: 'bg-slate-100 text-slate-500 font-semibold', tr: 'odd:bg-white even:bg-slate-50 hover:bg-blue-50 transition-colors' }"
                >
                  <template #issue_date-cell="{ row: { original: row } }">{{ fmtDate(row.issue_date) }}</template>
                  <template #wo-description-cell="{ row: { original: row } }">
                    <span class="block max-w-[220px] truncate" :title="row.description ?? ''">{{ row.description ?? "—" }}</span>
                  </template>
                  <template #status-cell="{ row: { original: row } }">
                    <UBadge :color="woStatusColors[row.status] ?? 'neutral'" variant="subtle" size="sm">
                      {{ row.status.replace(/_/g, " ") }}
                    </UBadge>
                  </template>
                  <template #asset_id-cell="{ row: { original: row } }">{{ row.asset_id ?? "—" }}</template>
                  <template #wo-actions-cell="{ row: { original: row } }">
                    <UButton variant="ghost" size="xs" icon="i-heroicons-eye" :to="`/work-orders/${row.work_order_id}`" />
                  </template>
                </UTable>
                <div v-if="sortedWOs.length === 0" class="py-6 text-center text-sm text-slate-400">No work orders found</div>
                <div v-if="woVisible < sortedWOs.length" class="flex justify-center pt-2">
                  <UButton variant="outline" size="sm" @click="woVisible += PAGE_SIZE">
                    Load more ({{ sortedWOs.length - woVisible }} remaining)
                  </UButton>
                </div>
              </template>
            </template>

            <!-- Invoices tab -->
            <template v-else-if="activeRelatedTab === 'invoices'">
              <div v-if="relatedLoading" class="flex items-center justify-center py-8 text-sm text-slate-400">Loading…</div>
              <template v-else>
                <UTable
                  :data="visibleInvoices"
                  :columns="invoiceColumns"
                  :ui="{ th: 'bg-slate-100 text-slate-500 font-semibold', tr: 'odd:bg-white even:bg-slate-50 hover:bg-blue-50 transition-colors' }"
                >
                  <template #invoice_date-cell="{ row: { original: row } }">{{ fmtDate(row.invoice_date) }}</template>
                  <template #inv-description-cell="{ row: { original: row } }">
                    <span class="block max-w-[180px] truncate" :title="row.description ?? ''">{{ row.description ?? "—" }}</span>
                  </template>
                  <template #invoice_type-cell="{ row: { original: row } }">{{ row.invoice_type.replace(/_/g, " ") }}</template>
                  <template #status-cell="{ row: { original: row } }">
                    <UBadge :color="invoiceStatusColors[row.status] ?? 'neutral'" variant="subtle" size="sm">
                      {{ row.status.replace(/_/g, " ") }}
                    </UBadge>
                  </template>
                  <template #subtotal-cell="{ row: { original: row } }">${{ row.subtotal.toLocaleString("en-US", { minimumFractionDigits: 2 }) }}</template>
                  <template #inv-actions-cell="{ row: { original: row } }">
                    <UButton variant="ghost" size="xs" icon="i-heroicons-eye" :to="`/finance/invoice/${row.id}`" />
                  </template>
                </UTable>
                <div v-if="sortedInvoices.length === 0" class="py-6 text-center text-sm text-slate-400">No invoices found</div>
                <div v-if="invVisible < sortedInvoices.length" class="flex justify-center pt-2">
                  <UButton variant="outline" size="sm" @click="invVisible += PAGE_SIZE">
                    Load more ({{ sortedInvoices.length - invVisible }} remaining)
                  </UButton>
                </div>
              </template>
            </template>

            <!-- Purchase Orders tab -->
            <template v-else-if="activeRelatedTab === 'purchase-orders'">
              <div v-if="relatedLoading" class="flex items-center justify-center py-8 text-sm text-slate-400">Loading…</div>
              <template v-else>
                <UTable
                  :data="visiblePOs"
                  :columns="poColumns"
                  :ui="{ th: 'bg-slate-100 text-slate-500 font-semibold', tr: 'odd:bg-white even:bg-slate-50 hover:bg-blue-50 transition-colors' }"
                >
                  <template #po_date-cell="{ row: { original: row } }">{{ fmtDate(row.po_date) }}</template>
                  <template #po-description-cell="{ row: { original: row } }">
                    <span class="block max-w-[220px] truncate" :title="row.description ?? ''">{{ row.description ?? "—" }}</span>
                  </template>
                  <template #po_type-cell="{ row: { original: row } }">{{ row.po_type.replace(/_/g, " ") }}</template>
                  <template #subtotal-cell="{ row: { original: row } }">${{ row.subtotal.toLocaleString("en-US", { minimumFractionDigits: 2 }) }}</template>
                  <template #po-actions-cell="{ row: { original: row } }">
                    <UButton variant="ghost" size="xs" icon="i-heroicons-eye" :to="`/finance/po/${row.po_no}`" />
                  </template>
                </UTable>
                <div v-if="sortedPOs.length === 0" class="py-6 text-center text-sm text-slate-400">No purchase orders found</div>
                <div v-if="poVisible < sortedPOs.length" class="flex justify-center pt-2">
                  <UButton variant="outline" size="sm" @click="poVisible += PAGE_SIZE">
                    Load more ({{ sortedPOs.length - poVisible }} remaining)
                  </UButton>
                </div>
              </template>
            </template>

          </div>

          <!-- Footer -->
          <div class="flex shrink-0 items-center justify-end gap-3 border-t border-gray-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
            <UButton :loading="saving" leading-icon="i-heroicons-check" @click="save">
              {{ isEditing ? "Save Changes" : "Create Supplier" }}
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Supplier</h3></template>
          <p class="text-sm text-slate-500">Delete supplier <strong>{{ deleteTarget?.name }}</strong>? This cannot be undone.</p>
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
