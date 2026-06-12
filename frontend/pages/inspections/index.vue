<script setup lang="ts">
import type { Inspection } from "~/types"

const { isAdmin } = useAuth()
const { getAll, getOne, create, update, remove, getTemplates } = useInspections()
const { getAll: getAssets } = useAssets()

const { data: inspections, refresh } = await useAsyncData("inspections", () => getAll())
const { data: templates } = await useAsyncData("insp-templates", () => getTemplates())
const { data: assets } = await useAsyncData("assets-select", () => getAssets())

const resultColors: Record<string, string> = { pass: "success", fail: "error", na: "neutral" }

const assetOptions = computed(() => (assets.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id })))
const templateOptions = computed(() => (templates.value ?? []).map((t) => ({ label: t.name, value: t.id })))
const resultOptions = ["pass", "fail", "na"]

const columns = [
  { accessorKey: "id", header: "ID" },
  { accessorKey: "inspection_no", header: "Inspection No" },
  { accessorKey: "asset_id", header: "Asset" },
  { accessorKey: "inspection_date", header: "Date" },
  { accessorKey: "overall_result", header: "Result" },
  { accessorKey: "submitted", header: "Submitted" },
  { id: "actions", header: "" },
]

const search = ref("")
const resultFilter = ref<string | null>(null)
const resultOptions2 = [{ label: "All", value: null }, ...resultOptions.map((r) => ({ label: r, value: r }))]

const filtered = computed(() =>
  (inspections.value ?? []).filter((i) => {
    const q = search.value.toLowerCase()
    const matchSearch = !q || (i.asset_id ?? "").toLowerCase().includes(q) || i.inspection_no.toLowerCase().includes(q)
    const matchResult = !resultFilter.value || i.overall_result === resultFilter.value
    return matchSearch && matchResult
  })
)

// ── Form modal ───────────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)

const defaultForm = (): Partial<Inspection> => ({
  overall_result: "pass",
  submitted: false,
  inspection_date: new Date().toISOString().slice(0, 10),
})
const form = ref<Partial<Inspection>>(defaultForm())

function openCreate() {
  form.value = defaultForm()
  isEditing.value = false
  editId.value = null
  formError.value = null
  showModal.value = true
}

async function openEdit(id: number) {
  form.value = { ...await getOne(id) }
  isEditing.value = true
  editId.value = id
  formError.value = null
  showModal.value = true
}

async function save() {
  saving.value = true
  formError.value = null
  try {
    if (isEditing.value && editId.value) {
      await update(editId.value, form.value as Inspection)
    } else {
      await create(form.value as Inspection)
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
const deleteTarget = ref<Inspection | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value?.id) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.id)
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
      <UButton leading-icon="i-heroicons-plus" @click="openCreate">New Inspection</UButton>
    </div>

    <UCard>
      <template #header>
        <div class="flex flex-wrap gap-3">
          <UInput v-model="search" placeholder="Search by asset or inspection no..." leading-icon="i-heroicons-magnifying-glass" class="max-w-xs" />
          <USelect v-model="resultFilter" :items="resultOptions2" placeholder="Filter by result" class="w-40" />
        </div>
      </template>
      <UTable :data="filtered" :columns="columns">
        <template #overall_result-cell="{ row: { original: row } }">
          <UBadge :color="resultColors[row.overall_result] ?? 'neutral'" variant="soft">{{ row.overall_result }}</UBadge>
        </template>
        <template #submitted-cell="{ row: { original: row } }">
          <UBadge :color="row.submitted ? 'success' : 'neutral'" variant="soft" size="sm">{{ row.submitted ? "Submitted" : "Draft" }}</UBadge>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-eye" @click="navigateTo(`/inspections/${row.id}`)" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEdit(row.id)" />
            <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Create / Edit Modal -->
    <UModal v-model:open="showModal">
      <template #content>
        <div class="w-full max-w-xl rounded-xl bg-white shadow-xl">
          <div class="flex items-start gap-4 border-b border-slate-100 px-6 py-5">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50">
              <UIcon name="i-heroicons-magnifying-glass" class="h-5 w-5 text-blue-600" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900">{{ isEditing ? "Edit Inspection" : "New Inspection" }}</h3>
              <p class="text-sm text-slate-500">{{ isEditing ? "Update inspection details" : "Record a new inspection" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>
          <div class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
            <UFormField label="Inspection No" required class="col-span-2">
              <UInput v-model="form.inspection_no" placeholder="e.g. INS-2024-001" class="w-full" />
            </UFormField>
            <UFormField label="Asset">
              <USelect v-model="form.asset_id" :items="assetOptions" placeholder="Select asset" class="w-full" />
            </UFormField>
            <UFormField label="Template">
              <USelect v-model="form.template_id" :items="templateOptions" placeholder="Select template" class="w-full" />
            </UFormField>
            <UFormField label="Inspection Date" required>
              <UInput v-model="form.inspection_date" type="date" class="w-full" />
            </UFormField>
            <UFormField label="Overall Result">
              <USelect v-model="form.overall_result" :items="resultOptions" class="w-full" />
            </UFormField>
            <UFormField label="Submitted" class="col-span-2">
              <UCheckbox v-model="form.submitted" label="Mark as submitted" />
            </UFormField>
            <UFormField label="Notes" class="col-span-2">
              <UTextarea v-model="form.notes" :rows="3" class="w-full" />
            </UFormField>
          </div>
          <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
            <UButton :loading="saving" @click="save">{{ isEditing ? "Save Changes" : "Create Inspection" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Inspection</h3></template>
          <p class="text-sm text-slate-500">Delete inspection <strong>{{ deleteTarget?.inspection_no }}</strong>? This cannot be undone.</p>
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
