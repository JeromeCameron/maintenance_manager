<script setup lang="ts">
import type { AssetPM } from "~/types"

const route = useRoute()
const router = useRouter()
const { getPM, createPM, updatePM, getPlans } = useMaintenance()
const { getAll: getAssets } = useAssets()

const isNew = route.params.id === "new"
const pmId = isNew ? null : Number(route.params.id)

const form = ref<Partial<AssetPM>>({ active: true })
const saving = ref(false)
const error = ref<string | null>(null)

const [assets, plans] = await Promise.all([
  useAsyncData("assets-select", () => getAssets()),
  useAsyncData("pm-plans", () => getPlans()),
])

if (!isNew && pmId) {
  const pm = await getPM(pmId)
  form.value = { ...pm }
}

const assetOptions = computed(() =>
  (assets.data.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id }))
)

const planOptions = computed(() =>
  (plans.data.value ?? []).map((p) => ({ label: `${p.pm_id} — ${p.description ?? p.frequency}`, value: p.pm_id }))
)

async function save() {
  saving.value = true
  error.value = null
  try {
    if (isNew) {
      await createPM(form.value as AssetPM)
      router.push("/maintenance")
    } else {
      await updatePM(pmId!, form.value as AssetPM)
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
      <UButton to="/maintenance" variant="ghost" icon="i-heroicons-arrow-left" />
      <h1 class="text-2xl font-bold text-slate-900">
        {{ isNew ? "New PM Schedule" : `PM Schedule #${pmId}` }}
      </h1>
    </div>

    <UCard class="max-w-2xl">
      <template #header><h2 class="font-semibold">PM Details</h2></template>

      <form class="grid grid-cols-1 gap-4 sm:grid-cols-2" @submit.prevent="save">
        <UFormField label="Asset" required>
          <USelect v-model="form.asset_id" :items="assetOptions" placeholder="Select asset" />
        </UFormField>

        <UFormField label="PM Plan" required>
          <USelect v-model="form.pm_plan_id" :items="planOptions" placeholder="Select plan" />
        </UFormField>

        <UFormField label="Last Service Date">
          <UInput v-model="form.last_service" type="date" />
        </UFormField>

        <UFormField label="Next Service Date">
          <UInput v-model="form.next_service" type="date" />
        </UFormField>

        <UFormField label="Active" class="sm:col-span-2">
          <UCheckbox v-model="form.active" label="Schedule is active" />
        </UFormField>
      </form>

      <UAlert v-if="error" color="error" variant="soft" :description="error" class="mt-4" />

      <template #footer>
        <div class="flex justify-end gap-2">
          <UButton to="/maintenance" variant="ghost">Cancel</UButton>
          <UButton :loading="saving" @click="save">
            {{ isNew ? "Create Schedule" : "Save Changes" }}
          </UButton>
        </div>
      </template>
    </UCard>
  </div>
</template>
