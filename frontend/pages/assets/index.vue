<script setup lang="ts">
import type { Asset } from "~/types"

const { getAll, getOne, create, update, remove } = useAssets()
const { getAll: getLocations } = useLocations()

const { data: assets, refresh } = await useAsyncData("assets", () => getAll())
const { data: locations } = await useAsyncData("locations-select", () => getLocations())

const statusColors: Record<string, string> = {
  operational: "success", maintenance: "warning", out_of_service: "error", disposed: "neutral",
}

const locationMap = computed(() => {
  const m: Record<number, string> = {}
  for (const l of locations.value ?? []) { if (l.location_id != null) m[l.location_id] = l.name }
  return m
})

const locationOptions = computed(() => (locations.value ?? []).map((l) => ({ label: l.name, value: l.location_id })))

const columns = [
  { accessorKey: "asset_id", header: "Asset ID" },
  { accessorKey: "manufacturer", header: "Manufacturer" },
  { accessorKey: "category", header: "Category" },
  { accessorKey: "status", header: "Status" },
  { accessorKey: "owned", header: "Ownership" },
  { accessorKey: "location_id", header: "Location" },
  { id: "actions", header: "" },
]

const statusOptions = ["operational", "maintenance", "out_of_service", "disposed"]
const categoryOptions = ["baler", "conveyor", "bobcat", "forklift", "scale"]
const ownershipOptions = ["owned", "rented", "leased"]

const search = ref("")
const filtered = computed(() =>
  (assets.value ?? []).filter((a) => {
    const q = search.value.toLowerCase()
    return !q || a.asset_id.toLowerCase().includes(q) || a.manufacturer.toLowerCase().includes(q)
  })
)

// ── Form modal ───────────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const editId = ref<string | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)

const defaultForm = (): Partial<Asset> => ({ status: "operational", owned: "owned", category: "baler" })
const form = ref<Partial<Asset>>(defaultForm())

function openCreate() {
  form.value = defaultForm()
  isEditing.value = false
  editId.value = null
  formError.value = null
  showModal.value = true
}

async function openEdit(id: string) {
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
      await update(editId.value, form.value as Asset)
    } else {
      await create(form.value as Asset)
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
const deleteTarget = ref<Asset | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.asset_id)
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
      <h1 class="text-2xl font-bold text-slate-900">Assets</h1>
      <UButton leading-icon="i-heroicons-plus" @click="openCreate">New Asset</UButton>
    </div>

    <UCard>
      <template #header>
        <UInput v-model="search" placeholder="Search by ID or manufacturer..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
      </template>
      <UTable :data="filtered" :columns="columns">
        <template #status-cell="{ row: { original: row } }">
          <UBadge :color="statusColors[row.status] ?? 'neutral'" variant="soft">{{ row.status.replace(/_/g, " ") }}</UBadge>
        </template>
        <template #category-cell="{ row: { original: row } }">
          <span class="capitalize">{{ row.category }}</span>
        </template>
        <template #owned-cell="{ row: { original: row } }">
          <span class="capitalize">{{ row.owned }}</span>
        </template>
        <template #location_id-cell="{ row: { original: row } }">
          {{ row.location_id ? locationMap[row.location_id] ?? row.location_id : "—" }}
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEdit(row.asset_id)" />
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
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50">
              <UIcon name="i-heroicons-wrench-screwdriver" class="h-5 w-5 text-blue-600" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900">{{ isEditing ? `Edit Asset: ${editId}` : "New Asset" }}</h3>
              <p class="text-sm text-slate-500">{{ isEditing ? "Update asset details" : "Register a new asset" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>
          <div class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
            <UFormField label="Asset ID" required>
              <UInput v-model="form.asset_id" placeholder="e.g. BAL-001" :disabled="isEditing" class="w-full" />
            </UFormField>
            <UFormField label="Manufacturer" required>
              <UInput v-model="form.manufacturer" placeholder="e.g. Caterpillar" class="w-full" />
            </UFormField>
            <UFormField label="Alias">
              <UInput v-model="form.alias" placeholder="e.g. Big Blue Baler" class="w-full" />
            </UFormField>
            <UFormField label="Category">
              <USelect v-model="form.category" :items="categoryOptions" class="w-full" />
            </UFormField>
            <UFormField label="Status">
              <USelect v-model="form.status" :items="statusOptions" class="w-full" />
            </UFormField>
            <UFormField label="Ownership">
              <USelect v-model="form.owned" :items="ownershipOptions" class="w-full" />
            </UFormField>
            <UFormField label="Location">
              <USelect v-model="form.location_id" :items="locationOptions" placeholder="Select location" class="w-full" />
            </UFormField>
            <UFormField label="Model No.">
              <UInput v-model="form.model_no" class="w-full" />
            </UFormField>
            <UFormField label="Serial No.">
              <UInput v-model="form.serial_no" class="w-full" />
            </UFormField>
            <UFormField label="Year">
              <UInput v-model.number="form.yr" type="number" class="w-full" />
            </UFormField>
            <UFormField label="Date In Service">
              <UInput v-model="form.date_in_service" type="date" class="w-full" />
            </UFormField>
            <UFormField label="Notes" class="col-span-2">
              <UTextarea v-model="form.notes" :rows="3" class="w-full" />
            </UFormField>
          </div>
          <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
            <UButton :loading="saving" @click="save">{{ isEditing ? "Save Changes" : "Create Asset" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Asset</h3></template>
          <p class="text-sm text-slate-500">Delete asset <strong>{{ deleteTarget?.asset_id }}</strong>? This cannot be undone.</p>
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
