<script setup lang="ts">
import type { Location } from "~/types"

const route = useRoute()
const router = useRouter()
const { getOne, create, update } = useLocations()

const isNew = route.params.id === "new"
const locId = isNew ? null : Number(route.params.id)

const form = ref<Partial<Location>>({
  typ: "depot",
  shift_depot: false,
  shift_length: 8,
})
const saving = ref(false)
const error = ref<string | null>(null)

if (!isNew && locId) {
  const loc = await getOne(locId)
  form.value = { ...loc }
}

const typeOptions = ["depot", "redemption_centre"]

async function save() {
  saving.value = true
  error.value = null
  try {
    if (isNew) {
      await create(form.value as Location)
      router.push("/locations")
    } else {
      await update(locId!, form.value as Location)
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
      <UButton to="/locations" variant="ghost" icon="i-heroicons-arrow-left" />
      <h1 class="text-2xl font-bold text-slate-900">
        {{ isNew ? "New Location" : `Location: ${form.name}` }}
      </h1>
    </div>

    <UCard class="max-w-2xl">
      <template #header><h2 class="font-semibold">Location Details</h2></template>

      <form class="grid grid-cols-1 gap-4 sm:grid-cols-2" @submit.prevent="save">
        <UFormField label="Name" required>
          <UInput v-model="form.name" placeholder="e.g. Kingston Depot" />
        </UFormField>

        <UFormField label="Type" required>
          <USelect v-model="form.typ" :items="typeOptions" />
        </UFormField>

        <UFormField label="Parish" required>
          <UInput v-model="form.parish" placeholder="e.g. St. Andrew" />
        </UFormField>

        <UFormField label="Supervisor" required>
          <UInput v-model="form.supervisor" />
        </UFormField>

        <UFormField label="Contact No" required>
          <UInput v-model="form.contact_no" type="tel" />
        </UFormField>

        <UFormField label="Shift Length (hrs)">
          <UInput v-model.number="form.shift_length" type="number" />
        </UFormField>

        <UFormField label="Latitude">
          <UInput v-model="form.latitude" placeholder="e.g. 17.9971" />
        </UFormField>

        <UFormField label="Longitude">
          <UInput v-model="form.longitude" placeholder="e.g. -76.7936" />
        </UFormField>

        <UFormField label="Shift Depot" class="sm:col-span-2">
          <UCheckbox v-model="form.shift_depot" label="This is a shift depot" />
        </UFormField>
      </form>

      <UAlert v-if="error" color="error" variant="soft" :description="error" class="mt-4" />

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton to="/locations" variant="ghost">Cancel</UButton>
          <UButton :loading="saving" @click="save">
            {{ isNew ? "Create Location" : "Save Changes" }}
          </UButton>
        </div>
      </template>
    </UCard>
  </div>
</template>
