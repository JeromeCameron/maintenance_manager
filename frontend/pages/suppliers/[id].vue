<script setup lang="ts">
import type { Supplier } from "~/types"

const route = useRoute()
const router = useRouter()
const { getOne, create, update } = useSuppliers()

const isNew = route.params.id === "new"
const supplierId = isNew ? null : Number(route.params.id)

const form = ref<Partial<Supplier>>({})
const saving = ref(false)
const error = ref<string | null>(null)

if (!isNew && supplierId) {
  const supplier = await getOne(supplierId)
  form.value = { ...supplier }
}

async function save() {
  saving.value = true
  error.value = null
  try {
    if (isNew) {
      await create(form.value as Supplier)
      router.push("/suppliers")
    } else {
      await update(supplierId!, form.value as Supplier)
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
      <UButton to="/suppliers" variant="ghost" icon="i-heroicons-arrow-left" />
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ isNew ? "New Supplier" : form.name }}
      </h1>
    </div>

    <UCard class="max-w-xl">
      <template #header><h2 class="font-semibold">Supplier Details</h2></template>

      <form class="grid grid-cols-1 gap-4" @submit.prevent="save">
        <UFormField label="Name" required>
          <UInput v-model="form.name" placeholder="Supplier company name" />
        </UFormField>

        <UFormField label="Primary Contact" required>
          <UInput v-model="form.primary_contact" placeholder="Contact person name" />
        </UFormField>

        <UFormField label="Email" required>
          <UInput v-model="form.email" type="email" />
        </UFormField>

        <UFormField label="Address" required>
          <UTextarea v-model="form.address" :rows="3" />
        </UFormField>
      </form>

      <UAlert v-if="error" color="error" variant="soft" :description="error" class="mt-4" />

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton to="/suppliers" variant="ghost">Cancel</UButton>
          <UButton :loading="saving" @click="save">
            {{ isNew ? "Create Supplier" : "Save Changes" }}
          </UButton>
        </div>
      </template>
    </UCard>
  </div>
</template>
