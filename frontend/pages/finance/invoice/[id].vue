<script setup lang="ts">
import type { Invoice } from "~/types"

const route = useRoute()
const router = useRouter()
const { getInvoice, createInvoice, updateInvoice } = useFinance()
const { getAll: getAssets } = useAssets()
const { getAll: getSuppliers } = useSuppliers()
const { getAll: getLocations } = useLocations()

const isNew = route.params.id === "new"
const invoiceId = isNew ? null : Number(route.params.id)

const form = ref<Partial<Invoice>>({
  status: "processing",
  invoice_type: "parts",
  subtotal: 0,
  tax_cert: false,
})
const saving = ref(false)
const error = ref<string | null>(null)

const [assets, suppliers, locations] = await Promise.all([
  useAsyncData("assets-select", () => getAssets()),
  useAsyncData("suppliers-select", () => getSuppliers()),
  useAsyncData("locations-select", () => getLocations()),
])

if (!isNew && invoiceId) {
  const inv = await getInvoice(invoiceId)
  form.value = { ...inv }
}

const assetOptions = computed(() =>
  (assets.data.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id }))
)
const supplierOptions = computed(() =>
  (suppliers.data.value ?? []).map((s) => ({ label: s.name, value: s.supplier_id }))
)
const locationOptions = computed(() =>
  (locations.data.value ?? []).map((l) => ({ label: l.name, value: l.location_id }))
)

const statusOptions = ["processing", "submitted", "on_hold"]
const typeOptions = ["parts", "parts_and_labour", "labour", "consumables", "services"]

async function save() {
  saving.value = true
  error.value = null
  try {
    if (isNew) {
      await createInvoice(form.value as Invoice)
      router.push("/finance")
    } else {
      await updateInvoice(invoiceId!, form.value as Invoice)
    }
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-3">
      <UButton to="/finance" variant="ghost" icon="i-heroicons-arrow-left" />
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ isNew ? "New Invoice" : `Invoice #${invoiceId}` }}
      </h1>
    </div>

    <UCard class="max-w-2xl">
      <template #header><h2 class="font-semibold">Invoice Details</h2></template>

      <form class="grid grid-cols-1 gap-4 sm:grid-cols-2" @submit.prevent="save">
        <UFormField label="Invoice No" required>
          <UInput v-model="form.invoice_no" placeholder="e.g. INV-2024-001" />
        </UFormField>

        <UFormField label="Job Date">
          <UInput v-model="form.job_date" type="date" />
        </UFormField>

        <UFormField label="Received Date">
          <UInput v-model="form.rec_date" type="date" />
        </UFormField>

        <UFormField label="Supplier">
          <USelect v-model="form.supplier_id" :items="supplierOptions" placeholder="Select supplier" />
        </UFormField>

        <UFormField label="Asset">
          <USelect v-model="form.asset_id" :items="assetOptions" placeholder="Select asset" />
        </UFormField>

        <UFormField label="Location">
          <USelect v-model="form.location_id" :items="locationOptions" placeholder="Select location" />
        </UFormField>

        <UFormField label="PO No">
          <UInput v-model="form.po_no" placeholder="Linked PO" />
        </UFormField>

        <UFormField label="Work Order ID">
          <UInput v-model.number="form.work_order_id" type="number" />
        </UFormField>

        <UFormField label="Invoice Type">
          <USelect v-model="form.invoice_type" :items="typeOptions" />
        </UFormField>

        <UFormField label="Status">
          <USelect v-model="form.status" :items="statusOptions" />
        </UFormField>

        <UFormField label="Subtotal" required>
          <UInput v-model.number="form.subtotal" type="number" step="0.01" />
        </UFormField>

        <UFormField label="Tax Certificate">
          <UCheckbox v-model="form.tax_cert" label="Tax certificate available" />
        </UFormField>

        <UFormField label="Description" class="sm:col-span-2">
          <UTextarea v-model="form.description" :rows="3" />
        </UFormField>
      </form>

      <UAlert v-if="error" color="error" variant="soft" :description="error" class="mt-4" />

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton to="/finance" variant="ghost">Cancel</UButton>
          <UButton :loading="saving" @click="save">
            {{ isNew ? "Create Invoice" : "Save Changes" }}
          </UButton>
        </div>
      </template>
    </UCard>
  </div>
</template>
