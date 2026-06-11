<script setup lang="ts">
import type { Inspection, InspectionTemplateItem, InspectionResult } from "~/types"

const route = useRoute()
const router = useRouter()
const {
  getOne, create, update,
  getTemplates,
  getItemsByTemplate,
  getResultsByInspection, createResult, updateResult,
} = useInspections()
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

// ── Results ───────────────────────────────────────────────────
const templateItems = ref<InspectionTemplateItem[]>([])
const results = ref<InspectionResult[]>([])
const savingResults = ref(false)
const resultsError = ref<string | null>(null)

// Map of template_item_id → draft result
const resultDraft = ref<Record<number, Partial<InspectionResult>>>({})

if (!isNew && inspId && form.value.template_id) {
  const [items, existingResults] = await Promise.all([
    getItemsByTemplate(form.value.template_id),
    getResultsByInspection(inspId),
  ])
  templateItems.value = items ?? []
  results.value = existingResults ?? []
  for (const r of existingResults ?? []) {
    if (r.template_item_id != null) resultDraft.value[r.template_item_id] = { ...r }
  }
  // Initialise drafts for items without a saved result
  for (const item of templateItems.value) {
    if (item.id != null && !resultDraft.value[item.id]) {
      resultDraft.value[item.id] = { template_item_id: item.id, inspection_id: inspId, result: "pass" }
    }
  }
}

// When template changes on a new inspection, load its items
watch(() => form.value.template_id, async (tid) => {
  if (!tid) { templateItems.value = []; resultDraft.value = {}; return }
  templateItems.value = await getItemsByTemplate(tid)
  resultDraft.value = {}
  for (const item of templateItems.value) {
    if (item.id != null) {
      resultDraft.value[item.id] = { template_item_id: item.id, result: "pass" }
    }
  }
})

function autoOverallResult() {
  const drafts = Object.values(resultDraft.value)
  const items = templateItems.value
  for (const item of items) {
    if (item.id == null) continue
    const d = resultDraft.value[item.id]
    if (d?.result === "fail" && item.is_critical) return "fail"
  }
  if (drafts.some((d) => d.result === "fail")) return "fail"
  return "pass"
}

async function saveResults() {
  if (!inspId) return
  savingResults.value = true
  resultsError.value = null
  try {
    for (const [itemIdStr, draft] of Object.entries(resultDraft.value)) {
      const itemId = Number(itemIdStr)
      const existing = results.value.find((r) => r.template_item_id === itemId)
      if (existing?.id) {
        await updateResult(existing.id, { ...existing, ...draft } as InspectionResult)
      } else {
        const created = await createResult({ ...draft, inspection_id: inspId } as InspectionResult)
        results.value = [...results.value, created]
      }
    }
    form.value.overall_result = autoOverallResult()
    await update(inspId, form.value as Inspection)
  } catch (e: unknown) {
    resultsError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingResults.value = false
  }
}

const resultColors: Record<string, string> = { pass: "success", fail: "error", na: "neutral" }
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-3">
      <UButton to="/inspections" variant="ghost" icon="i-heroicons-arrow-left" />
      <h1 class="text-2xl font-bold text-slate-900">
        {{ isNew ? "New Inspection" : `Inspection #${form.inspection_no}` }}
      </h1>
    </div>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <!-- Form -->
      <div class="lg:col-span-2">
        <UCard>
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
              <UButton :loading="saving" @click="save">{{ isNew ? "Create Inspection" : "Save Changes" }}</UButton>
            </div>
          </template>
        </UCard>
      </div>

      <!-- Summary sidebar -->
      <div v-if="!isNew" class="space-y-4">
        <UCard>
          <template #header><h2 class="font-semibold">Summary</h2></template>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-slate-500">Overall Result</span>
              <UBadge :color="resultColors[form.overall_result ?? 'na'] ?? 'neutral'" variant="soft" size="xs">
                {{ form.overall_result ?? "—" }}
              </UBadge>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">Items</span>
              <span>{{ templateItems.length }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">Fails</span>
              <span class="font-semibold text-red-600">
                {{ Object.values(resultDraft).filter(r => r.result === 'fail').length }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-slate-500">Submitted</span>
              <UBadge :color="form.submitted ? 'success' : 'neutral'" variant="soft" size="xs">
                {{ form.submitted ? "Yes" : "No" }}
              </UBadge>
            </div>
          </div>
        </UCard>
      </div>
    </div>

    <!-- Checklist Results -->
    <UCard v-if="templateItems.length">
      <template #header>
        <div class="flex items-center justify-between">
          <h2 class="font-semibold">Checklist</h2>
          <UButton size="xs" :loading="savingResults" @click="saveResults">Save Results</UButton>
        </div>
      </template>

      <div class="divide-y divide-slate-100">
        <div
          v-for="item in templateItems"
          :key="item.id"
          class="grid grid-cols-1 gap-3 py-4 sm:grid-cols-3 sm:items-start"
        >
          <div class="sm:col-span-2">
            <div class="flex items-center gap-2">
              <span class="text-sm font-medium text-slate-800">{{ item.order ? `${item.order}.` : "" }} {{ item.question }}</span>
              <UBadge v-if="item.is_critical" color="error" variant="soft" size="xs">Critical</UBadge>
            </div>
            <span v-if="item.category" class="text-xs text-slate-400">{{ item.category }}</span>
          </div>

          <div class="space-y-2" v-if="item.id != null">
            <USelect
              v-model="resultDraft[item.id].result"
              :items="resultOptions"
              size="sm"
            />
            <UInput
              v-model="resultDraft[item.id].notes"
              placeholder="Notes…"
              size="sm"
            />
          </div>
        </div>
      </div>

      <UAlert v-if="resultsError" color="error" variant="soft" :description="resultsError" class="mt-4" />

      <template #footer>
        <div class="flex justify-end">
          <UButton :loading="savingResults" @click="saveResults">Save Results</UButton>
        </div>
      </template>
    </UCard>

    <UCard v-else-if="!isNew && form.template_id">
      <p class="text-sm text-slate-400 px-2 py-3">No checklist items on this template.</p>
    </UCard>
  </div>
</template>
