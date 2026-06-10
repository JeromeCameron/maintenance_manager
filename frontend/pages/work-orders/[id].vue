<script setup lang="ts">
import type { WorkOrder, WorkOrderPart } from "~/types"

const route = useRoute()
const router = useRouter()
const { getOne, create, update, getParts, addPart, removePart } = useWorkOrders()
const { getAll: getAssets } = useAssets()

const isNew = route.params.id === "new"
const woId = isNew ? null : Number(route.params.id)

const form = ref<Partial<WorkOrder>>({
  status: "requested",
  priority: "Low",
  typ: "corrective",
})

const saving = ref(false)
const error = ref<string | null>(null)

const { data: assets } = await useAsyncData("assets-select", () => getAssets())

const parts = ref<WorkOrderPart[]>([])

if (!isNew && woId) {
  const wo = await getOne(woId)
  form.value = { ...wo }
  const allParts = await getParts()
  parts.value = (allParts ?? []).filter((p) => p.work_order_id === woId)
}

async function save() {
  saving.value = true
  error.value = null
  try {
    if (isNew) {
      await create(form.value as WorkOrder)
      router.push("/work-orders")
    } else {
      await update(woId!, form.value as WorkOrder)
    }
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    saving.value = false
  }
}

const statusOptions = ["requested", "scheduled", "awaiting_parts", "awaiting_po", "in_progress", "on_hold", "cancelled", "completed", "closed"]
const priorityOptions = ["Low", "Medium", "High"]
const typeOptions = ["corrective", "predictive", "preventative", "inspection", "project"]

const assetOptions = computed(() =>
  (assets.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id }))
)

// Parts
const newPart = ref<Partial<WorkOrderPart>>({ quantity_used: 1 })
const addingPart = ref(false)

async function submitPart() {
  if (!woId || !newPart.value.part_no) return
  addingPart.value = true
  try {
    const created = await addPart({ ...newPart.value, work_order_id: woId } as WorkOrderPart)
    parts.value = [...parts.value, created]
    newPart.value = { quantity_used: 1 }
  } finally {
    addingPart.value = false
  }
}

async function deletePart(id: number) {
  await removePart(id)
  parts.value = parts.value.filter((p) => p.id !== id)
}

const partColumns = [
  { accessorKey: "part_no", header: "Part No" },
  { accessorKey: "quantity_used", header: "Qty" },
  { accessorKey: "unit_cost", header: "Unit Cost" },
  { accessorKey: "total_cost", header: "Total" },
  { id: "actions", header: "" },
]
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-3">
      <UButton to="/work-orders" variant="ghost" icon="i-heroicons-arrow-left" />
      <h1 class="text-2xl font-bold text-slate-900">
        {{ isNew ? "New Work Order" : `Work Order #${woId}` }}
      </h1>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <!-- Main form -->
      <div class="space-y-6 lg:col-span-2">
        <UCard>
          <template #header><h2 class="font-semibold">Details</h2></template>

          <form class="grid grid-cols-1 gap-4 sm:grid-cols-2" @submit.prevent="save">
            <UFormField label="Asset">
              <USelect v-model="form.asset_id" :items="assetOptions" placeholder="Select asset" />
            </UFormField>

            <UFormField label="Priority">
              <USelect v-model="form.priority" :items="priorityOptions" />
            </UFormField>

            <UFormField label="Type">
              <USelect v-model="form.typ" :items="typeOptions" />
            </UFormField>

            <UFormField label="Status">
              <USelect v-model="form.status" :items="statusOptions" />
            </UFormField>

            <UFormField label="Issue Date">
              <UInput v-model="form.issue_date" type="date" />
            </UFormField>

            <UFormField label="Expected Date">
              <UInput v-model="form.expected_date" type="date" />
            </UFormField>

            <UFormField label="Date Completed">
              <UInput v-model="form.date_completed" type="date" />
            </UFormField>

            <UFormField label="Estimated Hours">
              <UInput v-model.number="form.estimated_hours" type="number" step="0.5" />
            </UFormField>

            <UFormField label="Actual Hours">
              <UInput v-model.number="form.actual_hours" type="number" step="0.5" />
            </UFormField>

            <UFormField label="Estimated Cost">
              <UInput v-model.number="form.estimated_cost" type="number" step="0.01" />
            </UFormField>

            <UFormField label="Actual Cost">
              <UInput v-model.number="form.actual_cost" type="number" step="0.01" />
            </UFormField>

            <UFormField label="Description" class="sm:col-span-2">
              <UTextarea v-model="form.description" :rows="3" />
            </UFormField>

            <UFormField label="Notes" class="sm:col-span-2">
              <UTextarea v-model="form.notes" :rows="2" />
            </UFormField>
          </form>

          <UAlert v-if="error" color="error" variant="soft" :description="error" class="mt-4" />

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton to="/work-orders" variant="ghost">Cancel</UButton>
              <UButton :loading="saving" @click="save">
                {{ isNew ? "Create Work Order" : "Save Changes" }}
              </UButton>
            </div>
          </template>
        </UCard>

        <!-- Parts used -->
        <UCard v-if="!isNew">
          <template #header><h2 class="font-semibold">Parts Used</h2></template>

          <UTable :data="parts" :columns="partColumns">
            <template #actions-cell="{ row: { original: row } }">
              <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deletePart(row.id)" />
            </template>
          </UTable>

          <div class="mt-4 grid grid-cols-1 gap-3 border-t pt-4 dark:border-gray-700 sm:grid-cols-4">
            <UFormField label="Part No">
              <UInput v-model="newPart.part_no" placeholder="e.g. BLT-001" />
            </UFormField>
            <UFormField label="Qty">
              <UInput v-model.number="newPart.quantity_used" type="number" min="1" />
            </UFormField>
            <UFormField label="Unit Cost">
              <UInput v-model.number="newPart.unit_cost" type="number" step="0.01" />
            </UFormField>
            <div class="flex items-end">
              <UButton :loading="addingPart" @click="submitPart">Add Part</UButton>
            </div>
          </div>
        </UCard>
      </div>

      <!-- Status sidebar -->
      <div v-if="!isNew" class="space-y-4">
        <UCard>
          <template #header><h2 class="font-semibold">Summary</h2></template>
          <dl class="space-y-3 text-sm">
            <div class="flex justify-between">
              <dt class="text-gray-500">Status</dt>
              <dd class="font-medium capitalize">{{ form.status?.replace(/_/g, " ") }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">Priority</dt>
              <dd class="font-medium">{{ form.priority }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">Est. Hours</dt>
              <dd class="font-medium">{{ form.estimated_hours ?? "—" }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">Actual Hours</dt>
              <dd class="font-medium">{{ form.actual_hours ?? "—" }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">Est. Cost</dt>
              <dd class="font-medium">{{ form.estimated_cost != null ? `$${form.estimated_cost.toFixed(2)}` : "—" }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">Actual Cost</dt>
              <dd class="font-medium">{{ form.actual_cost != null ? `$${form.actual_cost.toFixed(2)}` : "—" }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500">Parts ({{ parts.length }})</dt>
              <dd class="font-medium">
                ${{ parts.reduce((s, p) => s + (p.total_cost ?? p.unit_cost ?? 0), 0).toFixed(2) }}
              </dd>
            </div>
          </dl>
        </UCard>
      </div>
    </div>
  </div>
</template>
