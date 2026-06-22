<script setup lang="ts">
import type { Location } from "~/types"

const { isAdmin } = useAuth()
const { getAll, getOne, create, update, remove } = useLocations()

const { data: locations, refresh } = await useAsyncData("locations", () => getAll())

const columns = [
  { accessorKey: "location_id", header: "ID" },
  { accessorKey: "name", header: "Name" },
  { accessorKey: "parish", header: "Parish" },
  { accessorKey: "typ", header: "Type" },
  { accessorKey: "supervisor", header: "Supervisor" },
  { accessorKey: "contact_no", header: "Contact" },
  { accessorKey: "shift_depot", header: "Shift Depot" },
  { id: "actions", header: "" },
]

const search = ref("")
const filtered = computed(() =>
  (locations.value ?? []).filter((l) => {
    const q = search.value.toLowerCase()
    return !q || l.name.toLowerCase().includes(q) || l.parish.toLowerCase().includes(q) || l.supervisor.toLowerCase().includes(q)
  })
)

const typeOptions = ["depot", "redemption_centre"]

// ── Form modal ───────────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)

const defaultForm = (): Partial<Location> => ({ typ: "depot", shift_depot: false, shift_length: 8 })
const form = ref<Partial<Location>>(defaultForm())

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
      await update(editId.value, form.value as Location)
    } else {
      await create(form.value as Location)
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
const deleteTarget = ref<Location | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value?.location_id) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.location_id)
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
          <UInput v-model="search" placeholder="Search by name, parish or supervisor..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
          <UButton leading-icon="i-heroicons-plus" @click="openCreate" class="!bg-blue-700 hover:!bg-blue-800">New Location</UButton>
        </div>
      </template>
      <UTable :data="filtered" :columns="columns" :ui="{ th: 'bg-slate-100 text-slate-500 font-semibold', tr: 'odd:bg-white even:bg-slate-50 hover:bg-blue-50 transition-colors' }">
        <template #typ-cell="{ row: { original: row } }">
          <UBadge :color="row.typ === 'depot' ? 'info' : 'neutral'" variant="soft" size="sm">{{ row.typ.replace(/_/g, " ") }}</UBadge>
        </template>
        <template #shift_depot-cell="{ row: { original: row } }">
          <UBadge v-if="row.shift_depot" color="success" variant="soft" size="sm">Yes</UBadge>
          <span v-else class="text-slate-400">—</span>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-eye" @click="openEdit(row.location_id)" />
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
              <UIcon name="i-heroicons-map-pin" class="h-5 w-5 text-blue-600" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900">{{ isEditing ? "Edit Location" : "New Location" }}</h3>
              <p class="text-sm text-slate-500">{{ isEditing ? "Update location details" : "Add a new location" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>
          <div class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
            <UFormField label="Name" required>
              <UInput v-model="form.name" placeholder="e.g. Kingston Depot" class="w-full" />
            </UFormField>
            <UFormField label="Type" required>
              <USelect v-model="form.typ" :items="typeOptions" class="w-full" />
            </UFormField>
            <UFormField label="Parish" required>
              <UInput v-model="form.parish" placeholder="e.g. St. Andrew" class="w-full" />
            </UFormField>
            <UFormField label="Supervisor" required>
              <UInput v-model="form.supervisor" class="w-full" />
            </UFormField>
            <UFormField label="Contact No" required>
              <UInput v-model="form.contact_no" type="tel" class="w-full" />
            </UFormField>
            <UFormField label="Shift Length (hrs)">
              <UInput v-model.number="form.shift_length" type="number" class="w-full" />
            </UFormField>
            <UFormField label="Latitude">
              <UInput v-model="form.latitude" placeholder="e.g. 17.9971" class="w-full" />
            </UFormField>
            <UFormField label="Longitude">
              <UInput v-model="form.longitude" placeholder="e.g. -76.7936" class="w-full" />
            </UFormField>
            <UFormField label="Shift Depot" class="col-span-2">
              <UCheckbox v-model="form.shift_depot" label="This is a shift depot" />
            </UFormField>
          </div>
          <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
            <UButton :loading="saving" @click="save">{{ isEditing ? "Save Changes" : "Create Location" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Location</h3></template>
          <p class="text-sm text-slate-500">Delete location <strong>{{ deleteTarget?.name }}</strong>? This cannot be undone.</p>
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
