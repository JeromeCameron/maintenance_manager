<script setup lang="ts">
import type { User } from "~/types"

const { getAll, remove } = useUsers()

const { data: users, refresh } = await useAsyncData("users", () => getAll())

const roleColors: Record<string, string> = {
  admin: "error",
  moderator: "warning",
  user: "neutral",
}

const columns = [
  { accessorKey: "id", header: "ID" },
  { accessorKey: "username", header: "Username" },
  { accessorKey: "firstname", header: "First Name" },
  { accessorKey: "lastname", header: "Last Name" },
  { accessorKey: "email", header: "Email" },
  { accessorKey: "role", header: "Role" },
  { accessorKey: "active", header: "Active" },
  { id: "actions", header: "" },
]

const search = ref("")
const filtered = computed(() =>
  (users.value ?? []).filter((u) => {
    const q = search.value.toLowerCase()
    return (
      !q ||
      u.username.toLowerCase().includes(q) ||
      u.firstname.toLowerCase().includes(q) ||
      u.lastname.toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q)
    )
  })
)

const deleteTarget = ref<User | null>(null)
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
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Users</h1>
      <UButton to="/users/new" leading-icon="i-heroicons-plus">New User</UButton>
    </div>

    <UCard>
      <template #header>
        <UInput
          v-model="search"
          placeholder="Search by name, username or email..."
          leading-icon="i-heroicons-magnifying-glass"
          class="max-w-sm"
        />
      </template>

      <UTable :data="filtered" :columns="columns">
        <template #role-cell="{ row }">
          <UBadge :color="roleColors[row.role] ?? 'neutral'" variant="soft" size="sm" class="capitalize">
            {{ row.role }}
          </UBadge>
        </template>
        <template #active-cell="{ row }">
          <UBadge :color="row.active ? 'success' : 'neutral'" variant="soft" size="sm">
            {{ row.active ? "Active" : "Inactive" }}
          </UBadge>
        </template>
        <template #email-cell="{ row }">
          <a :href="`mailto:${row.email}`" class="text-primary-600 hover:underline dark:text-primary-400">
            {{ row.email }}
          </a>
        </template>
        <template #actions-cell="{ row }">
          <div class="flex items-center gap-1">
            <UButton :to="`/users/${row.id}`" variant="ghost" size="xs" icon="i-heroicons-pencil" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete User</h3></template>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Delete user <strong>{{ deleteTarget?.username }}</strong>? This cannot be undone.
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
