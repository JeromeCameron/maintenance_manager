<script setup lang="ts">
import type { Asset, AssetModel, AssetScores, WorkOrder, Downtime, Inspection } from "~/types"

const route = useRoute()
const router = useRouter()
const { getOne, create, update, getWorkOrders, getDowntimes, getInspections,
  getScoreByAsset, createScore, updateScore, removeScore } = useAssets()
const { getOne: getModelOne } = useAssetModels()

const isNew = route.params.id === "new"
const assetId = isNew ? null : (route.params.id as string)

const form = ref<Partial<Asset>>({
  status: "operational",
  owned: "owned",
  category: "baler",
})

const saving = ref(false)
const error = ref<string | null>(null)

if (!isNew && assetId) {
  const asset = await getOne(assetId)
  form.value = { ...asset }
}

const { data: workOrders } = !isNew && assetId
  ? await useAsyncData(`wo-${assetId}`, () => getWorkOrders(assetId))
  : { data: ref([]) }

const { data: downtimes } = !isNew && assetId
  ? await useAsyncData(`dt-${assetId}`, () => getDowntimes(assetId))
  : { data: ref([]) }

const { data: inspections } = !isNew && assetId
  ? await useAsyncData(`ins-${assetId}`, () => getInspections(assetId))
  : { data: ref([]) }

// ── Baler model specs (read-only) ─────────────────────────────
const modelData = ref<AssetModel | null>(null)
if (!isNew && assetId && form.value.category === "baler" && form.value.model_no) {
  modelData.value = await getModelOne(form.value.model_no).catch(() => null)
}

// ── Asset Scores ─────────────────────────────────────────────
const scores = ref<AssetScores | null>(null)
const showScoresModal = ref(false)
const scoresForm = ref<Partial<AssetScores>>({})
const savingScores = ref(false)
const scoresError = ref<string | null>(null)

if (!isNew && assetId) {
  scores.value = await getScoreByAsset(assetId)
}

function openScoresEdit() {
  scoresForm.value = scores.value ? { ...scores.value } : { asset_id: assetId ?? undefined }
  scoresError.value = null
  showScoresModal.value = true
}

async function saveScores() {
  savingScores.value = true
  scoresError.value = null
  try {
    if (scores.value?.score_id) {
      scores.value = await updateScore(scores.value.score_id, scoresForm.value as AssetScores)
    } else {
      scores.value = await createScore({ ...scoresForm.value, asset_id: assetId ?? undefined } as AssetScores)
    }
    showScoresModal.value = false
  } catch (e: unknown) {
    scoresError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingScores.value = false
  }
}

async function deleteScores() {
  if (!scores.value?.score_id) return
  await removeScore(scores.value.score_id)
  scores.value = null
}

async function save() {
  saving.value = true
  error.value = null
  try {
    if (isNew) {
      await create(form.value as Asset)
      router.push("/assets")
    } else {
      await update(assetId!, form.value as Asset)
    }
  } catch (e: unknown) {
    error.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    saving.value = false
  }
}

const statusOptions = ["operational", "maintenance", "out_of_service", "disposed"]
const categoryOptions = ["baler", "conveyor", "bobcat", "forklift", "scale"]
const ownershipOptions = ["owned", "rented", "leased"]

const woStatusColors: Record<string, string> = {
  requested: "info", in_progress: "warning", completed: "success", on_hold: "neutral", cancelled: "error",
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-3">
      <UButton to="/assets" variant="ghost" icon="i-heroicons-arrow-left" />
      <h1 class="text-2xl font-bold text-slate-900">
        {{ isNew ? "New Asset" : `Asset: ${assetId}` }}
      </h1>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <!-- Form -->
      <div class="lg:col-span-2">
        <UCard>
          <template #header>
            <h2 class="font-semibold">Asset Details</h2>
          </template>

          <form class="grid grid-cols-1 gap-4 sm:grid-cols-2" @submit.prevent="save">
            <UFormField label="Asset ID" required>
              <UInput v-model="form.asset_id" placeholder="e.g. BAL-001" :disabled="!isNew" />
            </UFormField>

            <UFormField label="Manufacturer" required>
              <UInput v-model="form.manufacturer" placeholder="e.g. Caterpillar" />
            </UFormField>

            <UFormField label="Category">
              <USelect v-model="form.category" :items="categoryOptions" />
            </UFormField>

            <UFormField label="Status">
              <USelect v-model="form.status" :items="statusOptions" />
            </UFormField>

            <UFormField label="Ownership">
              <USelect v-model="form.owned" :items="ownershipOptions" />
            </UFormField>

            <UFormField label="Model No.">
              <UInput v-model="form.model_no" />
            </UFormField>

            <UFormField label="Serial No.">
              <UInput v-model="form.serial_no" />
            </UFormField>

            <UFormField label="Year">
              <UInput v-model.number="form.yr" type="number" />
            </UFormField>

            <UFormField label="Date In Service">
              <UInput v-model="form.date_in_service" type="date" />
            </UFormField>

            <UFormField label="Notes" class="sm:col-span-2">
              <UTextarea v-model="form.notes" :rows="3" />
            </UFormField>
          </form>

          <UAlert v-if="error" color="error" variant="soft" :description="error" class="mt-4" />

          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton to="/assets" variant="ghost">Cancel</UButton>
              <UButton :loading="saving" @click="save">
                {{ isNew ? "Create Asset" : "Save Changes" }}
              </UButton>
            </div>
          </template>
        </UCard>
      </div>

      <!-- Baler & Scores -->
      <div v-if="!isNew" class="lg:col-span-2 grid grid-cols-1 gap-6 sm:grid-cols-2">
        <!-- Baler Specs (read-only from model) -->
        <UCard v-if="form.category === 'baler'">
          <template #header>
            <div class="flex items-center justify-between">
              <h2 class="font-semibold">Baler Specs</h2>
              <p class="text-xs text-slate-400">Edit in Settings → Asset Models</p>
            </div>
          </template>
          <div v-if="modelData" class="space-y-2 text-sm">
            <div class="flex justify-between"><span class="text-slate-500">Type</span><span class="capitalize">{{ modelData.baler_type ?? "—" }}</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Size</span><span class="capitalize">{{ modelData.baler_size ?? "—" }}</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Bale Weight</span><span>{{ modelData.bale_weight != null ? `${modelData.bale_weight} kg` : "—" }}</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Bale Time</span><span>{{ modelData.bale_time != null ? `${modelData.bale_time} min` : "—" }}</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Ram Force</span><span>{{ modelData.ram_force != null ? `${modelData.ram_force} kN` : "—" }}</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Bale Size</span><span>{{ modelData.bale_size ?? "—" }}</span></div>
          </div>
          <p v-else class="text-sm text-slate-400">No model assigned or specs not set.</p>
        </UCard>

        <!-- Asset Scores -->
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <h2 class="font-semibold">Asset Scores</h2>
              <div class="flex gap-1">
                <UButton size="xs" variant="ghost" icon="i-heroicons-pencil" @click="openScoresEdit" />
                <UButton v-if="scores" size="xs" variant="ghost" icon="i-heroicons-trash" color="error" @click="deleteScores" />
              </div>
            </div>
          </template>
          <div v-if="scores" class="space-y-2 text-sm">
            <div class="flex justify-between"><span class="text-slate-500">Operational</span><span>{{ scores.operational_score ?? "—" }}</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Safety</span><span>{{ scores.safety_score ?? "—" }}</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Backup</span><span>{{ scores.backup_score ?? "—" }}</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Repair</span><span>{{ scores.repair_score ?? "—" }}</span></div>
            <div class="flex justify-between"><span class="text-slate-500">Usage</span><span>{{ scores.usage_score ?? "—" }}</span></div>
          </div>
          <p v-else class="text-sm text-slate-400">No scores recorded. <UButton variant="link" size="xs" @click="openScoresEdit">Add now</UButton></p>
        </UCard>
      </div>

      <!-- Stats sidebar -->
      <div v-if="!isNew" class="space-y-4">
        <UCard>
          <template #header><h2 class="font-semibold">Work Orders</h2></template>
          <div class="space-y-2">
            <div v-for="wo in workOrders?.slice(0, 5)" :key="wo.work_order_id" class="flex items-center justify-between text-sm">
              <span class="font-mono text-gray-600 dark:text-gray-400">#{{ wo.work_order_id }}</span>
              <UBadge :color="woStatusColors[wo.status] ?? 'neutral'" variant="soft" size="xs">
                {{ wo.status.replace(/_/g, " ") }}
              </UBadge>
            </div>
            <p v-if="!workOrders?.length" class="text-sm text-gray-400">No work orders.</p>
          </div>
          <template #footer>
            <UButton to="/work-orders" variant="ghost" size="xs" trailing-icon="i-heroicons-arrow-right">
              View all
            </UButton>
          </template>
        </UCard>

        <UCard>
          <template #header><h2 class="font-semibold">Recent Downtime</h2></template>
          <div class="space-y-2">
            <div v-for="dt in downtimes?.slice(0, 5)" :key="dt.downtime_id" class="flex items-center justify-between text-sm">
              <span class="text-gray-600 dark:text-gray-400">{{ dt.start_date }}</span>
              <span class="font-medium">{{ dt.downtime_hours }}h</span>
            </div>
            <p v-if="!downtimes?.length" class="text-sm text-gray-400">No downtime recorded.</p>
          </div>
        </UCard>

        <UCard>
          <template #header><h2 class="font-semibold">Recent Inspections</h2></template>
          <div class="space-y-2">
            <div v-for="ins in inspections?.slice(0, 5)" :key="ins.id" class="flex items-center justify-between text-sm">
              <span class="text-gray-600 dark:text-gray-400">{{ ins.inspection_date }}</span>
              <UBadge :color="ins.overall_result === 'pass' ? 'success' : ins.overall_result === 'fail' ? 'error' : 'neutral'" variant="soft" size="xs">
                {{ ins.overall_result }}
              </UBadge>
            </div>
            <p v-if="!inspections?.length" class="text-sm text-gray-400">No inspections recorded.</p>
          </div>
        </UCard>
      </div>
    </div>

    <!-- Asset Scores Modal -->
    <UModal v-model:open="showScoresModal">
      <template #content>
        <div class="w-full max-w-lg rounded-xl bg-white shadow-xl">
          <div class="flex items-center justify-between border-b border-slate-100 px-6 py-5">
            <h3 class="text-base font-semibold text-slate-900">{{ scores ? "Edit Asset Scores" : "Add Asset Scores" }}</h3>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showScoresModal = false" />
          </div>
          <div class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
            <UFormField label="Operational Score">
              <UInput v-model.number="scoresForm.operational_score" type="number" class="w-full" />
            </UFormField>
            <UFormField label="Safety Score">
              <UInput v-model.number="scoresForm.safety_score" type="number" class="w-full" />
            </UFormField>
            <UFormField label="Backup Score">
              <UInput v-model.number="scoresForm.backup_score" type="number" class="w-full" />
            </UFormField>
            <UFormField label="Repair Score">
              <UInput v-model.number="scoresForm.repair_score" type="number" class="w-full" />
            </UFormField>
            <UFormField label="Usage Score">
              <UInput v-model.number="scoresForm.usage_score" type="number" class="w-full" />
            </UFormField>
          </div>
          <UAlert v-if="scoresError" color="error" variant="soft" :description="scoresError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showScoresModal = false">Cancel</UButton>
            <UButton :loading="savingScores" @click="saveScores">Save</UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
