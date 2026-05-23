<script setup lang="ts">
import type { PurchaseOrder } from "~/types"

const route = useRoute()
const router = useRouter()
const { getPO, createPO, updatePO, getCostCentres } = useFinance()
const { getAll: getAssets } = useAssets()
const { getAll: getSuppliers } = useSuppliers()
const { getAll: getLocations } = useLocations()

const isNew = route.params.id === "new"
const poId = isNew ? null : (route.params.id as string)

const form = ref<Partial<PurchaseOrder>>({ po_type: "corrective", subtotal: 0 })
const saving = ref(false)
const error = ref<string | null>(null)

const [assets, suppliers, locations, costCentres] = await Promise.all([
  useAsyncData("assets-select", () => getAssets()),
  useAsyncData("suppliers-select", () => getSuppliers()),
  useAsyncData("locations-select", () => getLocations()),
  useAsyncData("cost-centres", () => getCostCentres()),
])

if (!isNew && poId) {
  const po = await getPO(poId)
  form.value = { ...po }
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
const costCentreOptions = computed(() =>
  (costCentres.data.value ?? []).map((c) => ({ label: `${c.gl_code} — ${c.description ?? ""}`, value: c.gl_code }))
)

const poTypeOptions = ["corrective", "predictive", "preventative", "consumables", "rental"]

async function save() {
  saving.value = true
  error.value = null
  try {
    if (isNew) {
      await createPO(form.value as PurchaseOrder)
      router.push("/finance")
    } else {
      await updatePO(poId!, form.value as PurchaseOrder)
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
        {{ isNew ? "New Purchase Order" : `PO: ${poId}` }}
      </h1>
    </div>

    <UCard class="max-w-2xl">
      <template #header><h2 class="font-semibold">Purchase Order Details</h2></template>

      <form class="grid grid-cols-1 gap-4 sm:grid-cols-2" @submit.prevent="save">
        <UFormField label="PO No" required>
          <UInput v-model="form.po_no" placeholder="e.g. PO-2024-001" :disabled="!isNew" />
        </UFormField>

        <UFormField label="PO Date">
          <UInput v-model="form.po_date" type="date" />
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

        <UFormField label="PO Type">
          <USelect v-model="form.po_type" :items="poTypeOptions" />
        </UFormField>

        <UFormField label="Cost Centre">
          <USelect v-model="form.cost_centre_id" :items="costCentreOptions" placeholder="Select cost centre" />
        </UFormField>

        <UFormField label="Subtotal" required>
          <UInput v-model.number="form.subtotal" type="number" step="0.01" />
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
            {{ isNew ? "Create PO" : "Save Changes" }}
          </UButton>
        </div>
      </template>
    </UCard>
  </div>
</template>
