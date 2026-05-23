<script setup lang="ts">
import type { Downtime } from "~/types"

const route = useRoute()
const router = useRouter()
const { getOne, create, update, getCauses } = useDowntime()
const { getAll: getAssets } = useAssets()

const isNew = route.params.id === "new"
const dtId = isNew ? null : Number(route.params.id)

const form = ref<Partial<Downtime>>({ planned: false })
const saving = ref(false)
const error = ref<string | null>(null)

const [assets, causes] = await Promise.all([
  useAsyncData("assets-select", () => getAssets()),
  useAsyncData("dt-causes", () => getCauses()),
])

if (!isNew && dtId) {
  const dt = await getOne(dtId)
  form.value = { ...dt }
}

const assetOptions = computed(() =>
  (assets.data.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id }))
)

const causeOptions = computed(() =>
  (causes.data.value ?? []).map((c) => ({ label: c.name, value: c.cause_id }))
)

async function save() {
  saving.value = true
  error.value = null
  try {
    if (isNew) {
      await create(form.value as Downtime)
      router.push("/downtime")
    } else {
      await update(dtId!, form.value as Downtime)
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
      <UButton to="/downtime" variant="ghost" icon="i-heroicons-arrow-left" />
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        {{ isNew ? "Log Downtime" : `Downtime #${dtId}` }}
      </h1>
    </div>

    <UCard class="max-w-3xl">
      <template #header><h2 class="font-semibold">Downtime Details</h2></template>

      <form class="grid grid-cols-1 gap-4 sm:grid-cols-2" @submit.prevent="save">
        <UFormField label="Asset">
          <USelect v-model="form.asset_id" :items="assetOptions" placeholder="Select asset" />
        </UFormField>

        <UFormField label="Cause">
          <USelect v-model="form.cause_id" :items="causeOptions" placeholder="Select cause" />
        </UFormField>

        <UFormField label="Start Date">
          <UInput v-model="form.start_date" type="date" />
        </UFormField>

        <UFormField label="Start Time">
          <UInput v-model="form.start_time" type="time" />
        </UFormField>

        <UFormField label="End Date">
          <UInput v-model="form.end_date" type="date" />
        </UFormField>

        <UFormField label="End Time">
          <UInput v-model="form.end_time" type="time" />
        </UFormField>

        <UFormField label="Downtime Hours">
          <UInput v-model.number="form.downtime_hours" type="number" step="0.25" />
        </UFormField>

        <UFormField label="Work Order">
          <UInput v-model="form.work_order" placeholder="WO reference" />
        </UFormField>

        <UFormField label="Component Affected">
          <UInput v-model="form.component_affected" />
        </UFormField>

        <UFormField label="Planned">
          <UCheckbox v-model="form.planned" label="Planned downtime" />
        </UFormField>

        <UFormField label="Temporary Fix">
          <UCheckbox v-model="form.temporary_fix" label="Temporary fix applied" />
        </UFormField>

        <UFormField label="Repeat Failure">
          <UCheckbox v-model="form.repeat_failure" label="Repeat failure" />
        </UFormField>

        <UFormField label="Root Cause" class="sm:col-span-2">
          <UTextarea v-model="form.root_cause" :rows="2" />
        </UFormField>

        <UFormField label="Corrective Action" class="sm:col-span-2">
          <UTextarea v-model="form.corrective_action" :rows="2" />
        </UFormField>

        <UFormField label="Details" class="sm:col-span-2">
          <UTextarea v-model="form.details" :rows="2" />
        </UFormField>
      </form>

      <UAlert v-if="error" color="error" variant="soft" :description="error" class="mt-4" />

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton to="/downtime" variant="ghost">Cancel</UButton>
          <UButton :loading="saving" @click="save">
            {{ isNew ? "Log Downtime" : "Save Changes" }}
          </UButton>
        </div>
      </template>
    </UCard>
  </div>
</template>
