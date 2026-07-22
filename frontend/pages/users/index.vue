<script setup lang="ts">
import type { User } from "~/types"

const { isAdmin } = useAuth()
const { getAll, getOne, create, update, remove } = useUsers()

const { data: users, refresh } = await useAsyncData("users", () => getAll())

const roleColors: Record<string, string> = { admin: "error", moderator: "warning", user: "neutral" }

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
    return !q || u.username.toLowerCase().includes(q) || u.firstname.toLowerCase().includes(q) || u.lastname.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
  })
)

// ── Form modal ───────────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)

const defaultForm = (): Partial<User> => ({ role: "user", active: true })
const form = ref<Partial<User>>(defaultForm())

function openCreate() {
  form.value = defaultForm()
  isEditing.value = false
  editId.value = null
  formError.value = null
  showModal.value = true
}

async function openEdit(id: number) {
  const user = await getOne(id)
  const { password: _, ...rest } = user
  form.value = rest
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
      const payload = { ...form.value }
      if (!payload.password) delete payload.password
      await update(editId.value, payload as User)
    } else {
      await create(form.value as User)
    }
    await refresh()
    showModal.value = false
  } catch (e: unknown) {
    formError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    saving.value = false
  }
}

const roleOptions = ["admin", "moderator", "user"]

// ── Delete modal ─────────────────────────────────────────────
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
    <UCard>
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <UInput v-model="search" placeholder="Search by name, username or email..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
          <UButton leading-icon="i-heroicons-plus" @click="openCreate" class="!bg-blue-700 hover:!bg-blue-800">New User</UButton>
        </div>
      </template>
      <UTable :data="filtered" :columns="columns" :ui="{ th: 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 font-semibold', tr: 'odd:bg-white dark:odd:bg-slate-900 even:bg-slate-50 dark:even:bg-slate-800 hover:bg-blue-50 dark:hover:bg-blue-500/10 transition-colors' }">
        <template #role-cell="{ row: { original: row } }">
          <UBadge :color="roleColors[row.role] ?? 'neutral'" variant="soft" size="sm" class="capitalize">{{ row.role }}</UBadge>
        </template>
        <template #active-cell="{ row: { original: row } }">
          <UBadge :color="row.active ? 'success' : 'neutral'" variant="soft" size="sm">{{ row.active ? "Active" : "Inactive" }}</UBadge>
        </template>
        <template #email-cell="{ row: { original: row } }">
          <a :href="`mailto:${row.email}`" class="text-primary-600 hover:underline">{{ row.email }}</a>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-eye" @click="openEdit(row.id)" />
            <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Create / Edit Modal -->
    <UModal v-model:open="showModal">
      <template #content>
        <div class="w-full max-w-xl rounded-xl bg-white dark:bg-slate-900 shadow-xl">
          <div class="flex items-start gap-4 border-b border-slate-100 dark:border-slate-800 px-6 py-5">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 dark:bg-blue-500/10">
              <UIcon name="i-heroicons-users" class="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">{{ isEditing ? "Edit User" : "New User" }}</h3>
              <p class="text-sm text-slate-500 dark:text-slate-400">{{ isEditing ? "Update user account details" : "Create a new system account" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>
          <div class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
            <UFormField label="Username" required>
              <UInput v-model="form.username" placeholder="e.g. jsmith" class="w-full" />
            </UFormField>
            <UFormField label="Role" required>
              <USelect v-model="form.role" :items="roleOptions" class="w-full" />
            </UFormField>
            <UFormField label="First Name" required>
              <UInput v-model="form.firstname" class="w-full" />
            </UFormField>
            <UFormField label="Last Name" required>
              <UInput v-model="form.lastname" class="w-full" />
            </UFormField>
            <UFormField label="Email" required class="col-span-2">
              <UInput v-model="form.email" type="email" class="w-full" />
            </UFormField>
            <UFormField :label="isEditing ? 'New Password (leave blank to keep)' : 'Password'" :required="!isEditing" class="col-span-2">
              <UInput v-model="form.password" type="password" autocomplete="new-password" class="w-full" />
            </UFormField>
            <UFormField label="Active" class="col-span-2">
              <UCheckbox v-model="form.active" label="Account is active" />
            </UFormField>
          </div>
          <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 dark:border-slate-800 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
            <UButton :loading="saving" @click="save">{{ isEditing ? "Save Changes" : "Create User" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete User</h3></template>
          <p class="text-sm text-slate-500 dark:text-slate-400">Delete user <strong>{{ deleteTarget?.username }}</strong>? This cannot be undone.</p>
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
