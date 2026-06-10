<script setup lang="ts">
import type { User } from "~/types"

const route = useRoute()
const router = useRouter()
const { getOne, create, update } = useUsers()

const isNew = route.params.id === "new"
const userId = isNew ? null : Number(route.params.id)

const form = ref<Partial<User>>({
  role: "user",
  active: true,
})
const saving = ref(false)
const error = ref<string | null>(null)

if (!isNew && userId) {
  const user = await getOne(userId)
  // Don't populate password field when editing
  const { password: _, ...rest } = user
  form.value = { ...rest }
}

const roleOptions = ["admin", "moderator", "user"]

async function save() {
  saving.value = true
  error.value = null
  try {
    if (isNew) {
      await create(form.value as User)
      router.push("/users")
    } else {
      // Only send password if it was explicitly set
      const payload = { ...form.value }
      if (!payload.password) delete payload.password
      await update(userId!, payload as User)
    }
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-3">
      <UButton to="/users" variant="ghost" icon="i-heroicons-arrow-left" />
      <h1 class="text-2xl font-bold text-slate-900">
        {{ isNew ? "New User" : `User: ${form.username}` }}
      </h1>
    </div>

    <UCard class="max-w-xl">
      <template #header><h2 class="font-semibold">User Details</h2></template>

      <form class="grid grid-cols-1 gap-4 sm:grid-cols-2" @submit.prevent="save">
        <UFormField label="Username" required>
          <UInput v-model="form.username" placeholder="e.g. jsmith" />
        </UFormField>

        <UFormField label="Role" required>
          <USelect v-model="form.role" :items="roleOptions" />
        </UFormField>

        <UFormField label="First Name" required>
          <UInput v-model="form.firstname" />
        </UFormField>

        <UFormField label="Last Name" required>
          <UInput v-model="form.lastname" />
        </UFormField>

        <UFormField label="Email" required class="sm:col-span-2">
          <UInput v-model="form.email" type="email" />
        </UFormField>

        <UFormField :label="isNew ? 'Password' : 'New Password (leave blank to keep)'" :required="isNew" class="sm:col-span-2">
          <UInput v-model="form.password" type="password" autocomplete="new-password" />
        </UFormField>

        <UFormField label="Active" class="sm:col-span-2">
          <UCheckbox v-model="form.active" label="Account is active" />
        </UFormField>
      </form>

      <UAlert v-if="error" color="error" variant="soft" :description="error" class="mt-4" />

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton to="/users" variant="ghost">Cancel</UButton>
          <UButton :loading="saving" @click="save">
            {{ isNew ? "Create User" : "Save Changes" }}
          </UButton>
        </div>
      </template>
    </UCard>
  </div>
</template>
