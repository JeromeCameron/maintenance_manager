<script setup lang="ts">
import type { Part, StockTransaction } from "~/types"

const route = useRoute()
const router = useRouter()
const { getPart, createPart, updatePart, getCategories, getStockLevels, getTransactions, createTransaction } = useInventory()

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
const stockLevels = ref<{ location_id?: number; quantity: number }[]>([])
const transactions = ref<StockTransaction[]>([])

if (!isNew && partNo) {
  const [part, allStock, allTx] = await Promise.all([
    getPart(partNo),
    getStockLevels(),
    getTransactions(),
  ])
  form.value = { ...part }
  stockLevels.value = (allStock ?? []).filter((s) => s.part_no === partNo)
  transactions.value = (allTx ?? []).filter((t) => t.part_no === partNo).slice(0, 10)
}

const categoryOptions = computed(() =>
  (categories.value ?? []).map((c) => ({ label: c.name, value: c.id }))
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

// Stock adjustment
const adjustment = ref<Partial<StockTransaction>>({ transaction_type: "adjust", quantity: 0 })
const adjusting = ref(false)

async function submitAdjustment() {
  if (!partNo) return
  adjusting.value = true
  try {
    const tx = await createTransaction({ ...adjustment.value, part_no: partNo, transaction_date: new Date().toISOString().slice(0, 10) } as StockTransaction)
    transactions.value = [tx, ...transactions.value]
    adjustment.value = { transaction_type: "adjust", quantity: 0 }
  } finally {
    adjusting.value = false
  }
}

const txColumns = [
  { accessorKey: "transaction_date", header: "Date" },
  { accessorKey: "transaction_type", header: "Type" },
  { accessorKey: "quantity", header: "Qty" },
  { accessorKey: "notes", header: "Notes" },
]
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-3">
      <UButton to="/inventory" variant="ghost" icon="i-heroicons-arrow-left" />
      <h1 class="text-2xl font-bold text-slate-900">
        {{ isNew ? "New Part" : `Part: ${partNo}` }}
      </h1>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <!-- Form -->
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
              <UButton :loading="saving" @click="save">
                {{ isNew ? "Create Part" : "Save Changes" }}
              </UButton>
            </div>
          </template>
        </UCard>
      </div>

      <!-- Stock sidebar -->
      <div v-if="!isNew" class="space-y-4">
        <UCard>
          <template #header><h2 class="font-semibold">Stock Levels</h2></template>
          <div class="space-y-2 text-sm">
            <div v-for="s in stockLevels" :key="s.location_id" class="flex justify-between">
              <span class="text-gray-500">Location {{ s.location_id ?? "—" }}</span>
              <span class="font-semibold">{{ s.quantity }}</span>
            </div>
            <p v-if="!stockLevels.length" class="text-gray-400">No stock recorded.</p>
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

        <UCard>
          <template #header><h2 class="font-semibold">Recent Transactions</h2></template>
          <UTable :data="transactions" :columns="txColumns" />
        </UCard>
      </div>
    </div>
  </div>
</template>
