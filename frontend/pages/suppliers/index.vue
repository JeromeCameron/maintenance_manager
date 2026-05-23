<script setup lang="ts">
import type { Supplier } from "~/types"

const { getAll, remove } = useSuppliers()

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
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Suppliers</h1>
      <UButton to="/suppliers/new" leading-icon="i-heroicons-plus">New Supplier</UButton>
    </div>

    <UCard>
      <template #header>
        <UInput
          v-model="search"
          placeholder="Search by name, contact or email..."
          leading-icon="i-heroicons-magnifying-glass"
          class="max-w-sm"
        />
      </template>

      <UTable :data="filtered" :columns="columns">
        <template #email-cell="{ row }">
          <a :href="`mailto:${row.email}`" class="text-primary-600 hover:underline dark:text-primary-400">
            {{ row.email }}
          </a>
        </template>
        <template #actions-cell="{ row }">
          <div class="flex items-center gap-1">
            <UButton :to="`/suppliers/${row.supplier_id}`" variant="ghost" size="xs" icon="i-heroicons-pencil" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Supplier</h3></template>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Delete supplier <strong>{{ deleteTarget?.name }}</strong>? This cannot be undone.
          </p>
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
