<script setup lang="ts">
import type { Supplier, WorkOrder, Invoice, PurchaseOrder } from "~/types"

const route = useRoute()
const router = useRouter()
const { getOne, create, update } = useSuppliers()

const CATEGORY_OPTIONS = [
  { label: "Parts", value: "parts" },
  { label: "Services", value: "services" },
  { label: "Rental", value: "rental" },
  { label: "Safety Gears", value: "safety_gears" },
]

function toggleCategory(value: string) {
  const cats = form.value.categories ?? []
  form.value.categories = cats.includes(value)
    ? cats.filter((c) => c !== value)
    : [...cats, value]
}
const { getBySupplier: getWOsBySupplier } = useWorkOrders()
const { getInvoicesBySupplier, getPOsBySupplier } = useFinance()

const isNew = route.params.id === "new"
const supplierId = isNew ? null : Number(route.params.id)

const form = ref<Partial<Supplier>>({})
const saving = ref(false)
const error = ref<string | null>(null)

if (!isNew && supplierId) {
  const supplier = await getOne(supplierId)
  form.value = { ...supplier }
}

const { data: workOrders } = !isNew && supplierId
  ? await useAsyncData(`supplier-wo-${supplierId}`, () => getWOsBySupplier(supplierId!).catch(() => [] as WorkOrder[]))
  : { data: ref([] as WorkOrder[]) }

const { data: invoices } = !isNew && supplierId
  ? await useAsyncData(`supplier-inv-${supplierId}`, () => getInvoicesBySupplier(supplierId!).catch(() => [] as Invoice[]))
  : { data: ref([] as Invoice[]) }

const { data: pos } = !isNew && supplierId
  ? await useAsyncData(`supplier-po-${supplierId}`, () => getPOsBySupplier(supplierId!).catch(() => [] as PurchaseOrder[]))
  : { data: ref([] as PurchaseOrder[]) }

async function save() {
  saving.value = true
  error.value = null
  try {
    if (isNew) {
      await create(form.value as Supplier)
      router.push("/suppliers")
    } else {
      await update(supplierId!, form.value as Supplier)
    }
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    saving.value = false
  }
}

const PAGE_SIZE = 15
const activeTab = ref("work-orders")

const sortedWOs = computed(() =>
  [...(workOrders.value ?? [])].sort((a, b) => (b.issue_date ?? "").localeCompare(a.issue_date ?? ""))
)
const sortedInvoices = computed(() =>
  [...(invoices.value ?? [])].sort((a, b) => (b.invoice_date ?? "").localeCompare(a.invoice_date ?? ""))
)
const sortedPOs = computed(() =>
  [...(pos.value ?? [])].sort((a, b) => (b.po_date ?? "").localeCompare(a.po_date ?? ""))
)

const woVisible = ref(PAGE_SIZE)
const invVisible = ref(PAGE_SIZE)
const poVisible = ref(PAGE_SIZE)

const visibleWOs = computed(() => sortedWOs.value.slice(0, woVisible.value))
const visibleInvoices = computed(() => sortedInvoices.value.slice(0, invVisible.value))
const visiblePOs = computed(() => sortedPOs.value.slice(0, poVisible.value))

const woColumns = [
  { accessorKey: "work_order_id", header: "WO #" },
  { accessorKey: "issue_date", header: "Issued" },
  { id: "description", header: "Description" },
  { accessorKey: "status", header: "Status" },
  { accessorKey: "asset_id", header: "Asset" },
  { id: "actions", header: "" },
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
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-3">
      <UButton to="/suppliers" variant="ghost" icon="i-heroicons-arrow-left" />
      <h1 class="text-2xl font-bold text-slate-900">
        {{ isNew ? "New Supplier" : form.name }}
      </h1>
    </div>

    <UCard class="max-w-2xl">
      <template #header><h2 class="font-semibold">Supplier Details</h2></template>

      <form class="grid grid-cols-2 gap-x-5 gap-y-4" @submit.prevent="save">
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
          <UInput v-model="form.contact_number" placeholder="e.g. +1 876 xxx xxxx" class="w-full" />
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
              <UIcon
                :name="form.categories?.includes(opt.value) ? 'i-heroicons-check-circle' : 'i-heroicons-circle'"
                class="h-4 w-4"
              />
              {{ opt.label }}
            </label>
          </div>
        </UFormField>
      </form>

      <UAlert v-if="error" color="error" variant="soft" :description="error" class="mt-4" />

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton to="/suppliers" variant="ghost">Cancel</UButton>
          <UButton :loading="saving" @click="save">
            {{ isNew ? "Create Supplier" : "Save Changes" }}
          </UButton>
        </div>
      </template>
    </UCard>

    <!-- Related records tabs — only shown for existing suppliers -->
    <div v-if="!isNew">
      <div class="flex gap-2 border-b border-gray-200">
        <button
          v-for="tab in [
            { value: 'work-orders', label: 'Work Orders', count: sortedWOs.length },
            { value: 'invoices', label: 'Invoices', count: sortedInvoices.length },
            { value: 'purchase-orders', label: 'Purchase Orders', count: sortedPOs.length },
          ]"
          :key="tab.value"
          class="flex items-center gap-1.5 border-b-2 px-4 py-2 text-sm font-medium transition-colors"
          :class="activeTab === tab.value ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
          <span class="rounded-full bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">{{ tab.count }}</span>
        </button>
      </div>

      <!-- Work Orders -->
      <UCard v-if="activeTab === 'work-orders'">
        <UTable
          :data="visibleWOs"
          :columns="woColumns"
          :ui="{ th: 'bg-slate-100 text-slate-500 font-semibold', tr: 'odd:bg-white even:bg-slate-50 hover:bg-blue-50 transition-colors' }"
        >
          <template #issue_date-cell="{ row: { original: row } }">{{ fmtDate(row.issue_date) }}</template>
          <template #description-cell="{ row: { original: row } }">
            <span class="block max-w-[260px] truncate" :title="row.description ?? ''">{{ row.description ?? "—" }}</span>
          </template>
          <template #status-cell="{ row: { original: row } }">
            <UBadge :color="woStatusColors[row.status] ?? 'neutral'" variant="subtle" size="sm">
              {{ row.status.replace(/_/g, " ") }}
            </UBadge>
          </template>
          <template #asset_id-cell="{ row: { original: row } }">{{ row.asset_id ?? "—" }}</template>
          <template #actions-cell="{ row: { original: row } }">
            <UButton variant="ghost" size="xs" icon="i-heroicons-eye" :to="`/work-orders/${row.work_order_id}`" />
          </template>
        </UTable>
        <div v-if="sortedWOs.length === 0" class="py-8 text-center text-sm text-slate-400">No work orders found</div>
        <div v-if="woVisible < sortedWOs.length" class="mt-4 flex justify-center">
          <UButton variant="outline" size="sm" @click="woVisible += PAGE_SIZE">
            Load more ({{ sortedWOs.length - woVisible }} remaining)
          </UButton>
        </div>
      </UCard>

      <!-- Invoices -->
      <UCard v-else-if="activeTab === 'invoices'">
        <UTable
          :data="visibleInvoices"
          :columns="invoiceColumns"
          :ui="{ th: 'bg-slate-100 text-slate-500 font-semibold', tr: 'odd:bg-white even:bg-slate-50 hover:bg-blue-50 transition-colors' }"
        >
          <template #invoice_date-cell="{ row: { original: row } }">{{ fmtDate(row.invoice_date) }}</template>
          <template #inv-description-cell="{ row: { original: row } }">
            <span class="block max-w-[260px] truncate" :title="row.description ?? ''">{{ row.description ?? "—" }}</span>
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
        <div v-if="sortedInvoices.length === 0" class="py-8 text-center text-sm text-slate-400">No invoices found</div>
        <div v-if="invVisible < sortedInvoices.length" class="mt-4 flex justify-center">
          <UButton variant="outline" size="sm" @click="invVisible += PAGE_SIZE">
            Load more ({{ sortedInvoices.length - invVisible }} remaining)
          </UButton>
        </div>
      </UCard>

      <!-- Purchase Orders -->
      <UCard v-else-if="activeTab === 'purchase-orders'">
        <UTable
          :data="visiblePOs"
          :columns="poColumns"
          :ui="{ th: 'bg-slate-100 text-slate-500 font-semibold', tr: 'odd:bg-white even:bg-slate-50 hover:bg-blue-50 transition-colors' }"
        >
          <template #po_date-cell="{ row: { original: row } }">{{ fmtDate(row.po_date) }}</template>
          <template #po-description-cell="{ row: { original: row } }">
            <span class="block max-w-[260px] truncate" :title="row.description ?? ''">{{ row.description ?? "—" }}</span>
          </template>
          <template #po_type-cell="{ row: { original: row } }">{{ row.po_type.replace(/_/g, " ") }}</template>
          <template #subtotal-cell="{ row: { original: row } }">${{ row.subtotal.toLocaleString("en-US", { minimumFractionDigits: 2 }) }}</template>
          <template #po-actions-cell="{ row: { original: row } }">
            <UButton variant="ghost" size="xs" icon="i-heroicons-eye" :to="`/finance/po/${row.po_no}`" />
          </template>
        </UTable>
        <div v-if="sortedPOs.length === 0" class="py-8 text-center text-sm text-slate-400">No purchase orders found</div>
        <div v-if="poVisible < sortedPOs.length" class="mt-4 flex justify-center">
          <UButton variant="outline" size="sm" @click="poVisible += PAGE_SIZE">
            Load more ({{ sortedPOs.length - poVisible }} remaining)
          </UButton>
        </div>
      </UCard>
    </div>
  </div>
</template>
