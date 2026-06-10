<script setup lang="ts">
import type { Supplier } from "~/types"

const { getAll, getOne, create, update, remove } = useSuppliers()

const { data: suppliers, refresh } = await useAsyncData("suppliers", () => getAll())

const columns = [
  { accessorKey: "supplier_id", header: "ID" },
  { accessorKey: "name", header: "Name" },
  { accessorKey: "primary_contact", header: "Contact" },
  { accessorKey: "email", header: "Email" },
  { accessorKey: "address", header: "Address" },
  { id: "actions", header: "" },
]

const search = ref("")
const filtered = computed(() =>
  (suppliers.value ?? []).filter((s) => {
    const q = search.value.toLowerCase()
    return !q || s.name.toLowerCase().includes(q) || s.email.toLowerCase().includes(q) || s.primary_contact.toLowerCase().includes(q)
  })
)

// ── Form modal ───────────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)

const defaultForm = (): Partial<Supplier> => ({})
const form = ref<Partial<Supplier>>(defaultForm())

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
      <h1 class="text-2xl font-bold text-slate-900">Suppliers</h1>
      <UButton leading-icon="i-heroicons-plus" @click="openCreate">New Supplier</UButton>
    </div>

    <UCard>
      <template #header>
        <UInput v-model="search" placeholder="Search by name, contact or email..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
      </template>
      <UTable :data="filtered" :columns="columns">
        <template #email-cell="{ row: { original: row } }">
          <a :href="`mailto:${row.email}`" class="text-primary-600 hover:underline">{{ row.email }}</a>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEdit(row.supplier_id)" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Create / Edit Modal -->
    <UModal v-model:open="showModal">
      <template #content>
        <div class="w-full max-w-lg rounded-xl bg-white shadow-xl">
          <div class="flex items-start gap-4 border-b border-slate-100 px-6 py-5">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50">
              <UIcon name="i-heroicons-building-storefront" class="h-5 w-5 text-blue-600" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900">{{ isEditing ? "Edit Supplier" : "New Supplier" }}</h3>
              <p class="text-sm text-slate-500">{{ isEditing ? "Update supplier details" : "Add a new supplier" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>
          <div class="space-y-4 px-6 py-5">
            <UFormField label="Name" required>
              <UInput v-model="form.name" placeholder="Supplier company name" class="w-full" />
            </UFormField>
            <UFormField label="Primary Contact" required>
              <UInput v-model="form.primary_contact" placeholder="Contact person name" class="w-full" />
            </UFormField>
            <UFormField label="Email" required>
              <UInput v-model="form.email" type="email" class="w-full" />
            </UFormField>
            <UFormField label="Address" required>
              <UTextarea v-model="form.address" :rows="3" class="w-full" />
            </UFormField>
          </div>
          <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
            <UButton :loading="saving" @click="save">{{ isEditing ? "Save Changes" : "Create Supplier" }}</UButton>
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
