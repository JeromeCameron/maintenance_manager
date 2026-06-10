<script setup lang="ts">
import type { Downtime } from "~/types"

const { getAll, getOne, create, update, remove, getCauses } = useDowntime()
const { getAll: getAssets } = useAssets()

const { data: downtimes, refresh } = await useAsyncData("downtimes", () => getAll())
const { data: causes } = await useAsyncData("downtime-causes", () => getCauses())
const { data: assets } = await useAsyncData("assets-select", () => getAssets())

const causeMap = computed(() => {
  const m: Record<number, string> = {}
  for (const c of causes.value ?? []) { if (c.cause_id != null) m[c.cause_id] = c.name }
  return m
})

const causeOptions = computed(() => (causes.value ?? []).map((c) => ({ label: c.name, value: c.cause_id })))
const assetOptions = computed(() => (assets.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id })))

const columns = [
  { accessorKey: "downtime_id", header: "ID" },
  { accessorKey: "asset_id", header: "Asset" },
  { accessorKey: "cause_id", header: "Cause" },
  { accessorKey: "start_date", header: "Start" },
  { accessorKey: "downtime_hours", header: "Hours" },
  { accessorKey: "planned", header: "Planned" },
  { id: "actions", header: "" },
]

const search = ref("")
const filtered = computed(() =>
  (downtimes.value ?? []).filter((d) => {
    const q = search.value.toLowerCase()
    return !q || (d.asset_id ?? "").toLowerCase().includes(q) || String(d.downtime_id).includes(q)
  })
)

const totalHours = computed(() => (downtimes.value ?? []).reduce((s, d) => s + (d.downtime_hours ?? 0), 0))

// ── Form modal ───────────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)

const defaultForm = (): Partial<Downtime> => ({ planned: false })
const form = ref<Partial<Downtime>>(defaultForm())

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
      await update(editId.value, form.value as Downtime)
    } else {
      await create(form.value as Downtime)
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
const deleteTarget = ref<Downtime | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value?.downtime_id) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.downtime_id)
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
      <h1 class="text-2xl font-bold text-slate-900">Downtime</h1>
      <div class="flex items-center gap-3">
        <div class="rounded-lg bg-red-50 px-4 py-2 text-sm">
          <span class="text-red-600">Total: </span>
          <span class="font-bold text-red-700">{{ totalHours.toFixed(1) }}h</span>
        </div>
        <UButton leading-icon="i-heroicons-plus" @click="openCreate">Log Downtime</UButton>
      </div>
    </div>

    <UCard>
      <template #header>
        <UInput v-model="search" placeholder="Search by asset..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
      </template>
      <UTable :data="filtered" :columns="columns">
        <template #cause_id-cell="{ row: { original: row } }">{{ causeMap[row.cause_id] ?? "—" }}</template>
        <template #planned-cell="{ row: { original: row } }">
          <UBadge :color="row.planned ? 'info' : 'error'" variant="soft" size="sm">{{ row.planned ? "Planned" : "Unplanned" }}</UBadge>
        </template>
        <template #downtime_hours-cell="{ row: { original: row } }">
          <span class="font-medium">{{ row.downtime_hours?.toFixed(1) ?? "—" }}h</span>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEdit(row.downtime_id)" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Create / Edit Modal -->
    <UModal v-model:open="showModal">
      <template #content>
        <div class="w-full max-w-2xl rounded-xl bg-white shadow-xl">
          <div class="flex items-start gap-4 border-b border-slate-100 px-6 py-5">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-red-50">
              <UIcon name="i-heroicons-exclamation-triangle" class="h-5 w-5 text-red-500" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900">{{ isEditing ? "Edit Downtime Record" : "Log Downtime" }}</h3>
              <p class="text-sm text-slate-500">{{ isEditing ? "Update downtime details" : "Record an equipment downtime event" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>
          <div class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
            <UFormField label="Asset">
              <USelect v-model="form.asset_id" :items="assetOptions" placeholder="Select asset" class="w-full" />
            </UFormField>
            <UFormField label="Cause">
              <USelect v-model="form.cause_id" :items="causeOptions" placeholder="Select cause" class="w-full" />
            </UFormField>
            <UFormField label="Start Date">
              <UInput v-model="form.start_date" type="date" class="w-full" />
            </UFormField>
            <UFormField label="Start Time">
              <UInput v-model="form.start_time" type="time" class="w-full" />
            </UFormField>
            <UFormField label="End Date">
              <UInput v-model="form.end_date" type="date" class="w-full" />
            </UFormField>
            <UFormField label="End Time">
              <UInput v-model="form.end_time" type="time" class="w-full" />
            </UFormField>
            <UFormField label="Downtime Hours">
              <UInput v-model.number="form.downtime_hours" type="number" step="0.25" class="w-full" />
            </UFormField>
            <UFormField label="Work Order">
              <UInput v-model="form.work_order" placeholder="WO reference" class="w-full" />
            </UFormField>
            <UFormField label="Component Affected" class="col-span-2">
              <UInput v-model="form.component_affected" class="w-full" />
            </UFormField>
            <UFormField label="Planned">
              <UCheckbox v-model="form.planned" label="Planned downtime" />
            </UFormField>
            <UFormField label="Repeat Failure">
              <UCheckbox v-model="form.repeat_failure" label="Repeat failure" />
            </UFormField>
            <UFormField label="Root Cause" class="col-span-2">
              <UTextarea v-model="form.root_cause" :rows="2" class="w-full" />
            </UFormField>
            <UFormField label="Corrective Action" class="col-span-2">
              <UTextarea v-model="form.corrective_action" :rows="2" class="w-full" />
            </UFormField>
          </div>
          <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
            <UButton :loading="saving" @click="save">{{ isEditing ? "Save Changes" : "Log Downtime" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Downtime Record</h3></template>
          <p class="text-sm text-slate-500">Delete downtime record <strong>#{{ deleteTarget?.downtime_id }}</strong>? This cannot be undone.</p>
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
