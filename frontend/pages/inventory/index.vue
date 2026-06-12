<script setup lang="ts">
import type { Part } from "~/types"

const { isAdmin } = useAuth()
const { getParts, getPart, createPart, updatePart, removePart, getCategories, getStockLevels } = useInventory()

const { data: parts, refresh } = await useAsyncData("parts", () => getParts())
const { data: categories } = await useAsyncData("part-cats", () => getCategories())
const { data: stockLevels } = await useAsyncData("stock-levels", () => getStockLevels())

const catMap = computed(() => {
  const m: Record<number, string> = {}
  for (const c of categories.value ?? []) { if (c.id != null) m[c.id] = c.name }
  return m
})

const stockMap = computed(() => {
  const m: Record<string, number> = {}
  for (const s of stockLevels.value ?? []) { if (s.part_no) m[s.part_no] = (m[s.part_no] ?? 0) + s.quantity }
  return m
})

const categoryOptions = computed(() => (categories.value ?? []).map((c) => ({ label: c.name, value: c.id })))
const uomOptions = ["unit", "pieces", "gallons", "drums", "boxes", "pairs", "quart", "liter", "meter", "bag"]

const columns = [
  { accessorKey: "part_no", header: "Part No" },
  { accessorKey: "part_name", header: "Name" },
  { accessorKey: "manufacturer", header: "Manufacturer" },
  { accessorKey: "category_id", header: "Category" },
  { accessorKey: "unit_of_measure", header: "UOM" },
  { id: "stock", header: "Stock" },
  { accessorKey: "reorder_level", header: "Reorder At" },
  { accessorKey: "is_critical", header: "Critical" },
  { id: "actions", header: "" },
]

const search = ref("")
const filtered = computed(() =>
  (parts.value ?? []).filter((p) => {
    const q = search.value.toLowerCase()
    return !q || p.part_no.toLowerCase().includes(q) || p.part_name.toLowerCase().includes(q)
  })
)

const lowStock = computed(() => (parts.value ?? []).filter((p) => (stockMap.value[p.part_no] ?? 0) <= p.reorder_level))

// ── Form modal ───────────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const editId = ref<string | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)

const defaultForm = (): Partial<Part> => ({
  unit_of_measure: "unit", min_level: 0, max_level: 100,
  reorder_level: 10, reorder_qty: 20, is_critical: false, is_active: true,
})
const form = ref<Partial<Part>>(defaultForm())

function openCreate() {
  form.value = defaultForm()
  isEditing.value = false
  editId.value = null
  formError.value = null
  showModal.value = true
}

async function openEdit(partNo: string) {
  form.value = { ...await getPart(partNo) }
  isEditing.value = true
  editId.value = partNo
  formError.value = null
  showModal.value = true
}

async function save() {
  saving.value = true
  formError.value = null
  try {
    if (isEditing.value && editId.value) {
      await updatePart(editId.value, form.value as Part)
    } else {
      await createPart(form.value as Part)
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
const deleteTarget = ref<Part | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await removePart(deleteTarget.value.part_no)
    await refresh()
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <UButton leading-icon="i-heroicons-plus" @click="openCreate">New Part</UButton>
    </div>

    <UAlert v-if="lowStock.length" color="warning" variant="soft" icon="i-heroicons-exclamation-triangle"
      :title="`${lowStock.length} part${lowStock.length > 1 ? 's' : ''} at or below reorder level`" />

    <UCard>
      <template #header>
        <UInput v-model="search" placeholder="Search by part no or name..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
      </template>
      <UTable :data="filtered" :columns="columns">
        <template #category_id-cell="{ row: { original: row } }">{{ catMap[row.category_id] ?? "—" }}</template>
        <template #stock-cell="{ row: { original: row } }">
          <span :class="(stockMap[row.part_no] ?? 0) <= row.reorder_level ? 'font-semibold text-amber-600' : 'font-medium'">
            {{ stockMap[row.part_no] ?? 0 }}
          </span>
        </template>
        <template #is_critical-cell="{ row: { original: row } }">
          <UBadge v-if="row.is_critical" color="error" variant="soft" size="sm">Critical</UBadge>
          <span v-else class="text-slate-400">—</span>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-eye" @click="navigateTo(`/inventory/${row.part_no}`)" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEdit(row.part_no)" />
            <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Create / Edit Modal -->
    <UModal v-model:open="showModal">
      <template #content>
        <div class="w-full max-w-2xl rounded-xl bg-white shadow-xl">
          <div class="flex items-start gap-4 border-b border-slate-100 px-6 py-5">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50">
              <UIcon name="i-heroicons-archive-box" class="h-5 w-5 text-blue-600" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900">{{ isEditing ? `Edit Part: ${editId}` : "New Part" }}</h3>
              <p class="text-sm text-slate-500">{{ isEditing ? "Update part details" : "Add a new part to inventory" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>
          <div class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
            <UFormField label="Part No" required>
              <UInput v-model="form.part_no" placeholder="e.g. BLT-001" :disabled="isEditing" class="w-full" />
            </UFormField>
            <UFormField label="Part Name" required>
              <UInput v-model="form.part_name" class="w-full" />
            </UFormField>
            <UFormField label="Manufacturer">
              <UInput v-model="form.manufacturer" class="w-full" />
            </UFormField>
            <UFormField label="Category">
              <USelect v-model="form.category_id" :items="categoryOptions" placeholder="Select category" class="w-full" />
            </UFormField>
            <UFormField label="Unit of Measure">
              <USelect v-model="form.unit_of_measure" :items="uomOptions" class="w-full" />
            </UFormField>
            <UFormField label="Last Cost">
              <UInput v-model.number="form.last_cost" type="number" step="0.01" class="w-full" />
            </UFormField>
            <UFormField label="Min Level">
              <UInput v-model.number="form.min_level" type="number" class="w-full" />
            </UFormField>
            <UFormField label="Max Level">
              <UInput v-model.number="form.max_level" type="number" class="w-full" />
            </UFormField>
            <UFormField label="Reorder Level">
              <UInput v-model.number="form.reorder_level" type="number" class="w-full" />
            </UFormField>
            <UFormField label="Reorder Qty">
              <UInput v-model.number="form.reorder_qty" type="number" class="w-full" />
            </UFormField>
            <UFormField label="Critical">
              <UCheckbox v-model="form.is_critical" label="Critical part" />
            </UFormField>
            <UFormField label="Active">
              <UCheckbox v-model="form.is_active" label="Active" />
            </UFormField>
            <UFormField label="Description" class="col-span-2">
              <UTextarea v-model="form.description" :rows="2" class="w-full" />
            </UFormField>
          </div>
          <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
            <UButton :loading="saving" @click="save">{{ isEditing ? "Save Changes" : "Create Part" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Part</h3></template>
          <p class="text-sm text-slate-500">Delete part <strong>{{ deleteTarget?.part_no }}</strong>? This cannot be undone.</p>
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
