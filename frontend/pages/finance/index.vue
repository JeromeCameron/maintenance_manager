<script setup lang="ts">
const { getPOs, getInvoices, getBudgets, removePO, removeInvoice } = useFinance()

const { data: pos, refresh: refreshPOs } = await useAsyncData("pos", () => getPOs())
const { data: invoices, refresh: refreshInvoices } = await useAsyncData("invoices", () => getInvoices())
const { data: budgets } = await useAsyncData("budgets", () => getBudgets())

const activeTab = ref("pos")
const tabs = [
  { label: "Purchase Orders", value: "pos" },
  { label: "Invoices", value: "invoices" },
  { label: "Budgets", value: "budgets" },
]

const poColumns = [
  { accessorKey: "po_no", header: "PO No" },
  { accessorKey: "po_date", header: "Date" },
  { accessorKey: "asset_id", header: "Asset" },
  { accessorKey: "po_type", header: "Type" },
  { accessorKey: "cost_centre_id", header: "Cost Centre" },
  { accessorKey: "subtotal", header: "Subtotal" },
  { id: "actions", header: "" },
]

const invoiceColumns = [
  { accessorKey: "id", header: "ID" },
  { accessorKey: "invoice_no", header: "Invoice No" },
  { accessorKey: "job_date", header: "Job Date" },
  { accessorKey: "asset_id", header: "Asset" },
  { accessorKey: "invoice_type", header: "Type" },
  { accessorKey: "status", header: "Status" },
  { accessorKey: "subtotal", header: "Subtotal" },
  { id: "actions", header: "" },
]

const budgetColumns = [
  { accessorKey: "id", header: "ID" },
  { accessorKey: "gl_code", header: "GL Code" },
  { accessorKey: "financial_year", header: "FY" },
  { accessorKey: "month", header: "Month" },
  { accessorKey: "amount", header: "Amount" },
  { accessorKey: "notes", header: "Notes" },
]

const invoiceStatusColors: Record<string, string> = {
  processing: "info", submitted: "success", on_hold: "warning",
}

const search = ref("")
const filteredPOs = computed(() =>
  (pos.value ?? []).filter((p) => {
    const q = search.value.toLowerCase()
    return !q || p.po_no.toLowerCase().includes(q) || (p.asset_id ?? "").toLowerCase().includes(q)
  })
)
const filteredInvoices = computed(() =>
  (invoices.value ?? []).filter((i) => {
    const q = search.value.toLowerCase()
    return !q || i.invoice_no.toLowerCase().includes(q) || (i.asset_id ?? "").toLowerCase().includes(q)
  })
)

const totalPOValue = computed(() => (pos.value ?? []).reduce((s, p) => s + p.subtotal, 0))
const totalInvoiceValue = computed(() => (invoices.value ?? []).reduce((s, i) => s + i.subtotal, 0))

const deleteTarget = ref<{ type: "po" | "invoice"; id: string | number } | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    if (deleteTarget.value.type === "po") {
      await removePO(String(deleteTarget.value.id))
      await refreshPOs()
    } else {
      await removeInvoice(Number(deleteTarget.value.id))
      await refreshInvoices()
    }
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Finance</h1>
      <div class="flex gap-2">
        <UButton v-if="activeTab === 'pos'" to="/finance/po/new" leading-icon="i-heroicons-plus">New PO</UButton>
        <UButton v-if="activeTab === 'invoices'" to="/finance/invoice/new" leading-icon="i-heroicons-plus">New Invoice</UButton>
        <UButton v-if="activeTab === 'budgets'" to="/finance/budget/new" leading-icon="i-heroicons-plus">New Budget</UButton>
      </div>
    </div>

    <!-- KPIs -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <UCard>
        <div class="flex items-center gap-3">
          <UIcon name="i-heroicons-document-text" class="h-8 w-8 text-blue-500" />
          <div>
            <p class="text-xs text-gray-500">Total PO Value</p>
            <p class="text-xl font-bold">${{ totalPOValue.toLocaleString() }}</p>
          </div>
        </div>
      </UCard>
      <UCard>
        <div class="flex items-center gap-3">
          <UIcon name="i-heroicons-banknotes" class="h-8 w-8 text-green-500" />
          <div>
            <p class="text-xs text-gray-500">Total Invoice Value</p>
            <p class="text-xl font-bold">${{ totalInvoiceValue.toLocaleString() }}</p>
          </div>
        </div>
      </UCard>
      <UCard>
        <div class="flex items-center gap-3">
          <UIcon name="i-heroicons-calculator" class="h-8 w-8 text-purple-500" />
          <div>
            <p class="text-xs text-gray-500">Budget Entries</p>
            <p class="text-xl font-bold">{{ budgets?.length ?? 0 }}</p>
          </div>
        </div>
      </UCard>
    </div>

    <div class="flex gap-2 border-b border-gray-200 dark:border-gray-700">
      <button
        v-for="tab in tabs"
        :key="tab.value"
        class="border-b-2 px-4 py-2 text-sm font-medium transition-colors"
        :class="activeTab === tab.value
          ? 'border-primary-500 text-primary-600 dark:text-primary-400'
          : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'"
        @click="activeTab = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <UCard>
      <template v-if="activeTab !== 'budgets'" #header>
        <UInput
          v-model="search"
          placeholder="Search..."
          leading-icon="i-heroicons-magnifying-glass"
          class="max-w-sm"
        />
      </template>

      <!-- POs -->
      <UTable v-if="activeTab === 'pos'" :data="filteredPOs" :columns="poColumns">
        <template #subtotal-cell="{ row }">
          ${{ row.subtotal.toLocaleString() }}
        </template>
        <template #actions-cell="{ row }">
          <div class="flex items-center gap-1">
            <UButton :to="`/finance/po/${row.po_no}`" variant="ghost" size="xs" icon="i-heroicons-pencil" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = { type: 'po', id: row.po_no }" />
          </div>
        </template>
      </UTable>

      <!-- Invoices -->
      <UTable v-else-if="activeTab === 'invoices'" :data="filteredInvoices" :columns="invoiceColumns">
        <template #status-cell="{ row }">
          <UBadge :color="invoiceStatusColors[row.status] ?? 'neutral'" variant="soft">
            {{ row.status }}
          </UBadge>
        </template>
        <template #subtotal-cell="{ row }">
          ${{ row.subtotal.toLocaleString() }}
        </template>
        <template #actions-cell="{ row }">
          <div class="flex items-center gap-1">
            <UButton :to="`/finance/invoice/${row.id}`" variant="ghost" size="xs" icon="i-heroicons-pencil" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = { type: 'invoice', id: row.id }" />
          </div>
        </template>
      </UTable>

      <!-- Budgets -->
      <UTable v-else :data="budgets ?? []" :columns="budgetColumns">
        <template #amount-cell="{ row }">
          ${{ row.amount.toLocaleString() }}
        </template>
      </UTable>
    </UCard>

    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Confirm Delete</h3></template>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Delete <strong>{{ deleteTarget?.type === "po" ? "PO" : "Invoice" }} #{{ deleteTarget?.id }}</strong>? This cannot be undone.
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
