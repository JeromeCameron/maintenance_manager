<script setup lang="ts">
import type { Supplier } from "~/types"

const { isAdmin } = useAuth()
const { getAll, getOne, create, update, remove } = useSuppliers()

const { data: suppliers, refresh } = await useAsyncData("suppliers", () => getAll())

const columns = [
  { accessorKey: "supplier_id", header: "ID" },
  { accessorKey: "name", header: "Name" },
  { accessorKey: "contact_number", header: "Contact #" },
  { id: "categories", header: "Categories" },
  { id: "actions", header: "" },
]

const CATEGORY_OPTIONS = [
  { label: "Parts", value: "parts" },
  { label: "Services", value: "services" },
  { label: "Rental", value: "rental" },
  { label: "Safety Gears", value: "safety_gears" },
]

const search = ref("")
const filtered = computed(() =>
  (suppliers.value ?? [])
    .filter((s) => {
      const q = search.value.toLowerCase()
      return !q || s.name.toLowerCase().includes(q) || (s.contact_number ?? "").toLowerCase().includes(q)
    })
    .sort((a, b) => a.name.localeCompare(b.name))
)

// ── Form modal ───────────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)

const defaultForm = (): Partial<Supplier> => ({ categories: [] })
const form = ref<Partial<Supplier>>(defaultForm())

function toggleCategory(value: string) {
  const cats = form.value.categories ?? []
  form.value.categories = cats.includes(value)
    ? cats.filter((c) => c !== value)
    : [...cats, value]
}

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
      await update(editId.value, form.value as Supplier)
    } else {
      await create(form.value as Supplier)
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
const deleteTarget = ref<Supplier | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value?.supplier_id) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.supplier_id)
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
      <UButton leading-icon="i-heroicons-plus" @click="openCreate">New Supplier</UButton>
    </div>

    <UCard>
      <template #header>
        <UInput v-model="search" placeholder="Search by name or contact number..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
      </template>
      <UTable :data="filtered" :columns="columns" :ui="{ root: 'relative overflow-auto max-h-[calc(100vh-22rem)]' }">
        <template #categories-cell="{ row: { original: row } }">
          <div v-if="row.categories?.length" class="flex flex-wrap gap-1">
            <UBadge
              v-for="cat in row.categories"
              :key="cat"
              variant="soft"
              color="primary"
              class="capitalize"
            >
              {{ cat.replace(/_/g, " ") }}
            </UBadge>
          </div>
          <span v-else class="text-gray-400">—</span>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-eye" @click="openEdit(row.supplier_id)" />
            <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Create / Edit Modal -->
    <UModal v-model:open="showModal" :ui="{ content: 'max-w-lg' }">
      <template #content>
        <div class="flex max-h-[90vh] w-full max-w-lg flex-col rounded-xl bg-white shadow-xl">
          <!-- Header -->
          <div class="flex shrink-0 items-start gap-4 border-b border-gray-100 px-6 py-5">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50">
              <UIcon name="i-heroicons-building-storefront" class="h-5 w-5 text-blue-600" />
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="text-base font-semibold text-slate-900">{{ isEditing ? "Edit Supplier" : "New Supplier" }}</h3>
              <p class="mt-0.5 text-sm text-gray-500">{{ isEditing ? "Update supplier details" : "Add a new supplier" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>

          <!-- Scrollable body -->
          <div class="flex-1 overflow-y-auto px-6 py-5 space-y-4">
            <div class="grid grid-cols-2 gap-x-5 gap-y-4">
              <UFormField label="Name" required class="col-span-2">
                <UInput v-model="form.name" placeholder="Supplier company name" class="w-full" />
              </UFormField>
              <UFormField label="Primary Contact" required>
                <UInput v-model="form.primary_contact" placeholder="Contact person name" class="w-full" />
              </UFormField>
              <UFormField label="Contact Title">
                <UInput v-model="form.contact_title" placeholder="e.g. Account Manager" class="w-full" />
              </UFormField>
              <UFormField label="Contact Number">
                <UInput v-model="form.contact_number" placeholder="e.g. +61 4xx xxx xxx" class="w-full" />
              </UFormField>
              <UFormField label="Email" required>
                <UInput v-model="form.email" type="email" class="w-full" />
              </UFormField>
              <UFormField label="Address" required class="col-span-2">
                <UTextarea v-model="form.address" :rows="3" class="w-full" />
              </UFormField>
              <UFormField label="Notes" class="col-span-2">
                <UTextarea v-model="form.notes" :rows="3" placeholder="Additional notes…" class="w-full" />
              </UFormField>
              <UFormField label="Categories" class="col-span-2">
                <div class="flex flex-wrap gap-3 pt-1">
                  <label
                    v-for="opt in CATEGORY_OPTIONS"
                    :key="opt.value"
                    class="flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors"
                    :class="form.categories?.includes(opt.value)
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 text-gray-600 hover:border-gray-300'"
                    @click="toggleCategory(opt.value)"
                  >
                    <UIcon
                      :name="form.categories?.includes(opt.value) ? 'i-heroicons-check-circle' : 'i-heroicons-circle'"
                      class="h-4 w-4"
                    />
                    {{ opt.label }}
                  </label>
                </div>
              </UFormField>
            </div>
            <UAlert v-if="formError" color="error" variant="soft" :description="formError" />
          </div>

          <!-- Footer -->
          <div class="flex shrink-0 items-center justify-end gap-3 border-t border-gray-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
            <UButton :loading="saving" leading-icon="i-heroicons-check" @click="save">
              {{ isEditing ? "Save Changes" : "Create Supplier" }}
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Supplier</h3></template>
          <p class="text-sm text-slate-500">Delete supplier <strong>{{ deleteTarget?.name }}</strong>? This cannot be undone.</p>
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
