<script setup lang="ts">
import type { Inspection } from "~/types"

const route = useRoute()
const router = useRouter()
const { getOne, create, update, getTemplates } = useInspections()
const { getAll: getAssets } = useAssets()

const isNew = route.params.id === "new"
const inspId = isNew ? null : Number(route.params.id)

const form = ref<Partial<Inspection>>({
  overall_result: "pass",
  submitted: false,
  inspection_date: new Date().toISOString().slice(0, 10),
})
const saving = ref(false)
const error = ref<string | null>(null)

const [assets, templates] = await Promise.all([
  useAsyncData("assets-select", () => getAssets()),
  useAsyncData("insp-templates", () => getTemplates()),
])

if (!isNew && inspId) {
  const ins = await getOne(inspId)
  form.value = { ...ins }
}

const assetOptions = computed(() =>
  (assets.data.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id }))
)

const templateOptions = computed(() =>
  (templates.data.value ?? []).map((t) => ({ label: t.name, value: t.id }))
)

const resultOptions = ["pass", "fail", "na"]

async function save() {
  saving.value = true
  error.value = null
  try {
    if (isNew) {
      await create(form.value as Inspection)
      router.push("/inspections")
    } else {
      await update(inspId!, form.value as Inspection)
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
      <UButton to="/inspections" variant="ghost" icon="i-heroicons-arrow-left" />
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ isNew ? "New Inspection" : `Inspection #${inspId}` }}
      </h1>
    </div>

    <UCard class="max-w-2xl">
      <template #header><h2 class="font-semibold">Inspection Details</h2></template>

      <form class="grid grid-cols-1 gap-4 sm:grid-cols-2" @submit.prevent="save">
        <UFormField label="Inspection No" required>
          <UInput v-model="form.inspection_no" placeholder="e.g. INS-2024-001" />
        </UFormField>

        <UFormField label="Asset">
          <USelect v-model="form.asset_id" :items="assetOptions" placeholder="Select asset" />
        </UFormField>

        <UFormField label="Template">
          <USelect v-model="form.template_id" :items="templateOptions" placeholder="Select template" />
        </UFormField>

        <UFormField label="Inspection Date" required>
          <UInput v-model="form.inspection_date" type="date" />
        </UFormField>

        <UFormField label="Inspection Time">
          <UInput v-model="form.inspection_time" type="time" />
        </UFormField>

        <UFormField label="Overall Result">
          <USelect v-model="form.overall_result" :items="resultOptions" />
        </UFormField>

        <UFormField label="Submitted" class="sm:col-span-2">
          <UCheckbox v-model="form.submitted" label="Mark as submitted" />
        </UFormField>

        <UFormField v-if="form.submitted" label="Submitted Date">
          <UInput v-model="form.submitted_date" type="date" />
        </UFormField>

        <UFormField label="Notes" class="sm:col-span-2">
          <UTextarea v-model="form.notes" :rows="3" />
        </UFormField>
      </form>

      <UAlert v-if="error" color="error" variant="soft" :description="error" class="mt-4" />

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton to="/inspections" variant="ghost">Cancel</UButton>
          <UButton :loading="saving" @click="save">
            {{ isNew ? "Create Inspection" : "Save Changes" }}
          </UButton>
        </div>
      </template>
    </UCard>
  </div>
</template>
