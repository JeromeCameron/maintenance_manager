<script setup lang="ts">
import type { Downtime, DowntimeFactor } from "~/types"

const { isAdmin } = useAuth()
const {
  getAll, getOne, create, update, remove, getCauses,
  getFactorTypes, getFactors, getFactorsByDowntime, createFactor, updateFactor, removeFactor,
} = useDowntime()
const { getAll: getAssets } = useAssets()
const { getAll: getWorkOrders } = useWorkOrders()

const { data: downtimes, refresh } = await useAsyncData("downtimes", () => getAll())
const { data: causes } = await useAsyncData("downtime-causes", () => getCauses())
const { data: assets } = await useAsyncData("assets-select", () => getAssets())
const { data: workOrders } = await useAsyncData("downtime-work-orders", () => getWorkOrders())
const { data: factorTypes } = await useAsyncData("downtime-factor-types", () => getFactorTypes())
const { data: allFactors, refresh: refreshFactors } = await useAsyncData("downtime-all-factors", () => getFactors())

const factorTypeMap = computed(() => {
  const m: Record<number, string> = {}
  for (const t of factorTypes.value ?? []) { if (t.factor_type_id != null) m[t.factor_type_id] = t.name }
  return m
})
const factorTypeOptions = computed(() =>
  (factorTypes.value ?? []).filter((t) => t.active).map((t) => ({ label: t.name, value: t.factor_type_id }))
)

// Per-downtime rollup for the list badges: how many factors and how many delay hours.
const factorStats = computed(() => {
  const m: Record<number, { count: number; hours: number }> = {}
  for (const f of allFactors.value ?? []) {
    if (f.downtime_id == null) continue
    const rec = (m[f.downtime_id] ??= { count: 0, hours: 0 })
    rec.count++
    rec.hours += f.delay_hours ?? 0
  }
  return m
})

const causeMap = computed(() => {
  const m: Record<number, string> = {}
  for (const c of causes.value ?? []) { if (c.cause_id != null) m[c.cause_id] = c.name }
  return m
})

const causeOptions = computed(() => (causes.value ?? []).map((c) => ({ label: c.name, value: c.cause_id })))
const assetOptions = computed(() => [...(assets.value ?? [])].sort((a, b) => a.asset_id.localeCompare(b.asset_id)).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id })))
const workOrderOptions = computed(() =>
  [...(workOrders.value ?? [])]
    .sort((a, b) => (b.work_order_id ?? 0) - (a.work_order_id ?? 0))
    .map(w => ({ label: `#${w.work_order_id}${w.description ? ' — ' + w.description.slice(0, 50) : ''}`, value: String(w.work_order_id) }))
)

const search = ref("")
const filtered = computed(() =>
  (downtimes.value ?? [])
    .filter((d) => {
      const q = search.value.toLowerCase()
      return !q || (d.asset_id ?? "").toLowerCase().includes(q) || String(d.downtime_id).includes(q) || (causeMap.value[d.cause_id] ?? "").toLowerCase().includes(q)
    })
    .sort((a, b) => {
      const aOngoing = isOpen(a) ? 0 : 1
      const bOngoing = isOpen(b) ? 0 : 1
      if (aOngoing !== bOngoing) return aOngoing - bOngoing
      return new Date(b.start_date ?? "").getTime() - new Date(a.start_date ?? "").getTime()
    })
)

const totalHours = computed(() => (downtimes.value ?? []).reduce((s, d) => s + (d.downtime_hours ?? 0), 0))
const openCount = computed(() => (downtimes.value ?? []).filter(d => !d.end_date).length)

// ── Helpers ───────────────────────────────────────────────────
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
function formatDate(value: string | null | undefined): string {
  if (!value) return '—'
  const [year, month, day] = value.slice(0, 10).split('-').map(Number)
  if (!year || !month || !day) return '—'
  return `${String(day).padStart(2,'0')}-${MONTHS[month - 1]}-${String(year).slice(-2)}`
}

function isOpen(d: Downtime): boolean {
  return !d.end_date
}

// ── Form modal ───────────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)
const modalTab = ref<"details" | "factors">("details")

const defaultForm = (): Partial<Downtime> => ({ planned: false, shift_asset: false })
const form = ref<Partial<Downtime>>(defaultForm())

// ── Exacerbating factors (only editable once the downtime is saved) ──
const factors = ref<DowntimeFactor[]>([])
const emptyFactor = (): Partial<DowntimeFactor> => ({ resolved: false })
const factorDraft = ref<Partial<DowntimeFactor>>(emptyFactor())
const editingFactorId = ref<number | null>(null)
const savingFactor = ref(false)
const factorError = ref<string | null>(null)

// The backend derives delay_hours (shift/holiday aware) whenever a start date + time are set.
const factorAutoCalc = computed(() => !!(factorDraft.value.start_date && factorDraft.value.start_time))

const factorDelayHours = computed(() => factors.value.reduce((s, f) => s + (f.delay_hours ?? 0), 0))
const factorSortKey = (f: DowntimeFactor) =>
  f.start_date ? new Date(`${f.start_date}T${f.start_time ?? "00:00:00"}`).getTime() : -Infinity
const sortedFactors = computed(() => [...factors.value].sort((a, b) => factorSortKey(b) - factorSortKey(a)))
const effectiveRepairHours = computed(() => {
  const total = form.value.downtime_hours
  if (total == null) return null
  return Math.max(0, total - factorDelayHours.value)
})

function resetFactorDraft() {
  factorDraft.value = emptyFactor()
  editingFactorId.value = null
  factorError.value = null
}

function startEditFactor(f: DowntimeFactor) {
  editingFactorId.value = f.id ?? null
  factorDraft.value = { ...f }
  factorError.value = null
}

async function submitFactor() {
  if (!editId.value) return
  savingFactor.value = true
  factorError.value = null
  try {
    if (editingFactorId.value) {
      const updated = await updateFactor(editingFactorId.value, { ...factorDraft.value, downtime_id: editId.value } as DowntimeFactor)
      factors.value = factors.value.map((f) => (f.id === updated.id ? updated : f))
    } else {
      const created = await createFactor({ ...factorDraft.value, downtime_id: editId.value } as DowntimeFactor)
      factors.value = [...factors.value, created]
    }
    resetFactorDraft()
    await refreshFactors()
  } catch (e: unknown) {
    factorError.value = (e as { message?: string }).message ?? "Failed to save factor"
  } finally {
    savingFactor.value = false
  }
}

async function deleteFactor(id: number) {
  await removeFactor(id)
  factors.value = factors.value.filter((f) => f.id !== id)
  if (editingFactorId.value === id) resetFactorDraft()
  await refreshFactors()
}

function openCreate() {
  form.value = defaultForm()
  isEditing.value = false
  editId.value = null
  formError.value = null
  modalTab.value = "details"
  factors.value = []
  resetFactorDraft()
  showModal.value = true
}

async function openEdit(id: number) {
  form.value = { ...await getOne(id) }
  isEditing.value = true
  editId.value = id
  formError.value = null
  modalTab.value = "details"
  factors.value = []
  resetFactorDraft()
  showModal.value = true
  try {
    factors.value = await getFactorsByDowntime(id)
  } catch {
    factors.value = []
  }
}

async function save() {
  saving.value = true
  formError.value = null
  try {
    if (isEditing.value && editId.value) {
      await update(editId.value, form.value as Downtime)
    } else {
      await create(form.value as Downtime)
    }
    await refresh()
    showModal.value = false
  } catch (e: unknown) {
    formError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    saving.value = false
  }
}

// ── Delete modal ─────────────────────────────────────────────
const deleteTarget = ref<Downtime | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value?.downtime_id) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.downtime_id)
    await refresh()
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="flex min-h-full flex-col gap-4">

    <!-- KPI strip -->
    <div class="flex items-center gap-3">
      <div class="inline-flex items-center gap-1.5 rounded-lg bg-red-50 dark:bg-red-500/10 px-4 py-2 text-sm">
        <span class="text-red-500 dark:text-red-400">Total downtime:</span>
        <span class="font-bold text-red-700 dark:text-red-400">{{ totalHours.toFixed(1) }}h</span>
      </div>
      <div v-if="openCount > 0" class="inline-flex items-center gap-1.5 rounded-lg bg-orange-50 dark:bg-orange-500/10 px-4 py-2 text-sm">
        <UIcon name="i-heroicons-exclamation-circle" class="h-4 w-4 text-orange-500 dark:text-orange-400" />
        <span class="font-semibold text-orange-700 dark:text-orange-400">{{ openCount }} open</span>
        <span class="text-orange-500 dark:text-orange-400">— no end date recorded</span>
      </div>
    </div>

    <!-- List card -->
    <UCard :ui="{ root: 'flex flex-col flex-1 min-h-0', body: 'flex flex-col flex-1 min-h-0 p-0' }">
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <UInput v-model="search" placeholder="Search by asset, cause..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
          <UButton leading-icon="i-heroicons-plus" @click="openCreate" class="!bg-blue-700 hover:!bg-blue-800">Log Downtime</UButton>
        </div>
      </template>

      <div class="overflow-auto h-full p-4 space-y-2">
        <div v-if="filtered.length === 0" class="py-12 text-center text-sm text-gray-400 dark:text-slate-500">
          No downtime records found.
        </div>
        <template v-else>
          <div
            v-for="d in filtered"
            :key="d.downtime_id"
            class="flex cursor-pointer items-center gap-4 rounded-lg px-5 py-3.5 ring-1 ring-gray-200 dark:ring-slate-700 hover:bg-red-50/20 dark:hover:bg-red-500/10 transition-colors border-l-4"
            :class="isOpen(d) ? 'border-l-red-400' : 'border-l-transparent'"
            @click="openEdit(d.downtime_id)"
          >
            <!-- Icon -->
            <div
              class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full"
              :class="d.planned ? 'bg-blue-50 dark:bg-blue-500/10' : 'bg-red-50 dark:bg-red-500/10'"
            >
              <UIcon
                :name="d.planned ? 'i-heroicons-calendar' : 'i-heroicons-exclamation-triangle'"
                class="h-4 w-4"
                :class="d.planned ? 'text-blue-400' : 'text-red-400'"
              />
            </div>

            <!-- Asset + cause (fixed) -->
            <div class="w-52 shrink-0 min-w-0">
              <div class="flex items-center gap-1.5">
                <span class="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate">{{ d.asset_id ?? '—' }}</span>
                <span v-if="isOpen(d)" class="h-2 w-2 shrink-0 rounded-full bg-red-500" />
              </div>
              <p class="text-xs text-slate-500 dark:text-slate-400 truncate">{{ causeMap[d.cause_id] ?? 'Unknown cause' }}</p>
            </div>

            <!-- Details (fills remaining space) -->
            <p class="flex-1 min-w-0 truncate text-xs text-gray-400 dark:text-slate-500">{{ d.details ?? '—' }}</p>

            <!-- Pills + date -->
            <div class="flex shrink-0 items-center gap-2">
              <span
                class="inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium ring-1"
                :class="d.planned ? 'bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 ring-blue-200 dark:ring-blue-500/30' : 'bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 ring-red-200 dark:ring-red-500/30'"
              >{{ d.planned ? 'Planned' : 'Unplanned' }}</span>
              <span v-if="d.repeat_failure" class="inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium bg-amber-50 text-amber-600 ring-1 ring-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-500/30">Repeat</span>
              <span v-if="d.temporary_fix" class="inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium bg-purple-50 text-purple-600 ring-1 ring-purple-200 dark:bg-purple-500/10 dark:text-purple-400 dark:ring-purple-500/30">Temp fix</span>
              <span
                v-if="factorStats[d.downtime_id]"
                class="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium bg-orange-50 text-orange-600 ring-1 ring-orange-200 dark:bg-orange-500/10 dark:text-orange-400 dark:ring-orange-500/30"
                :title="`${factorStats[d.downtime_id].count} exacerbating factor(s), ${factorStats[d.downtime_id].hours.toFixed(1)}h attributable delay`"
              >
                <UIcon name="i-heroicons-clock" class="h-3 w-3" />
                {{ factorStats[d.downtime_id].hours > 0 ? factorStats[d.downtime_id].hours.toFixed(1) + 'h delay' : factorStats[d.downtime_id].count + ' factor' + (factorStats[d.downtime_id].count > 1 ? 's' : '') }}
              </span>
            </div>

            <!-- Start date -->
            <div class="w-28 shrink-0 text-center">
              <p class="text-xs text-gray-500 dark:text-slate-400">{{ formatDate(d.start_date) }}</p>
              <p v-if="d.start_time" class="text-[11px] text-gray-400 dark:text-slate-500">{{ d.start_time.slice(0, 5) }}</p>
            </div>

            <!-- Hours (prominent) -->
            <div class="w-16 shrink-0 text-right">
              <span class="text-lg font-bold leading-tight" :class="isOpen(d) ? 'text-red-600' : 'text-slate-700 dark:text-slate-300'">
                {{ d.downtime_hours != null ? d.downtime_hours.toFixed(1) : '—' }}
              </span>
              <span class="block text-[11px] font-medium text-gray-400 dark:text-slate-500 -mt-0.5">hours</span>
            </div>

            <!-- Open / closed + ID -->
            <div class="w-24 shrink-0 text-right">
              <span v-if="isOpen(d)" class="flex items-center justify-end gap-1 text-[11px] font-semibold text-red-500">
                <UIcon name="i-heroicons-exclamation-circle" class="h-3.5 w-3.5" />
                Open
              </span>
              <p v-else class="text-[11px] text-gray-400 dark:text-slate-500">Closed {{ formatDate(d.end_date) }}</p>
              <p class="text-[11px] text-gray-400 dark:text-slate-500 mt-0.5">#{{ d.downtime_id }}<template v-if="d.work_order"> · WO {{ d.work_order }}</template></p>
            </div>

            <!-- Actions -->
            <div v-if="isAdmin" class="flex shrink-0 items-center gap-1">
              <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click.stop="deleteTarget = d" />
            </div>
          </div>
        </template>
      </div>
    </UCard>

    <!-- Create / Edit Modal -->
    <UModal v-model:open="showModal">
      <template #content>
        <div class="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-xl bg-white dark:bg-slate-900 shadow-xl">
          <div class="flex shrink-0 items-start gap-4 border-b border-slate-100 dark:border-slate-800 px-6 py-5">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-red-50 dark:bg-red-500/10">
              <UIcon name="i-heroicons-exclamation-triangle" class="h-5 w-5 text-red-500 dark:text-red-400" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">{{ isEditing ? "Edit Downtime Record" : "Log Downtime" }}</h3>
              <p class="text-sm text-slate-500 dark:text-slate-400">{{ isEditing ? "Update downtime details" : "Record an equipment downtime event" }}</p>
              <div v-if="isEditing" class="mt-2 flex flex-wrap items-center gap-3 text-[11px] text-slate-500 dark:text-slate-400">
                <span>Total <strong class="text-slate-700 dark:text-slate-200">{{ form.downtime_hours != null ? form.downtime_hours.toFixed(1) : '—' }}h</strong></span>
                <span>Attributable delay <strong class="text-orange-600 dark:text-orange-400">{{ factorDelayHours.toFixed(1) }}h</strong></span>
                <span v-if="effectiveRepairHours != null">Effective repair <strong class="text-slate-700 dark:text-slate-200">{{ effectiveRepairHours.toFixed(1) }}h</strong></span>
              </div>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>

          <div class="flex shrink-0 gap-2 border-b border-slate-100 dark:border-slate-800 px-6">
            <button
              v-for="t in [{ label: 'Details', value: 'details' }, { label: `Factors${factors.length ? ` (${factors.length})` : ''}`, value: 'factors' }]"
              :key="t.value"
              type="button"
              class="border-b-2 px-1 py-2.5 text-sm font-medium transition-colors"
              :class="modalTab === t.value ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'"
              @click="modalTab = t.value as 'details' | 'factors'"
            >
              {{ t.label }}
            </button>
          </div>

          <div v-show="modalTab === 'details'" class="flex-1 overflow-y-auto px-6 py-5">
            <div class="grid grid-cols-2 gap-x-5 gap-y-4">
              <UFormField label="Asset">
                <USelect v-model="form.asset_id" :items="assetOptions" placeholder="Select asset" class="w-full" />
              </UFormField>
              <UFormField label="Cause">
                <USelect v-model="form.cause_id" :items="causeOptions" placeholder="Select cause" class="w-full" />
              </UFormField>
              <UFormField label="Start Date">
                <UInput v-model="form.start_date" type="date" class="w-full" />
              </UFormField>
              <UFormField label="Start Time">
                <UInput v-model="form.start_time" type="time" class="w-full" />
              </UFormField>
              <UFormField label="End Date">
                <UInput v-model="form.end_date" type="date" class="w-full" />
              </UFormField>
              <UFormField label="End Time">
                <UInput v-model="form.end_time" type="time" class="w-full" />
              </UFormField>
              <UFormField label="Downtime Hours">
                <UInput v-model.number="form.downtime_hours" type="number" step="0.25" class="w-full" />
              </UFormField>
              <UFormField label="Work Order">
                <USelect v-model="form.work_order" :items="workOrderOptions" placeholder="Select work order" class="w-full" />
              </UFormField>
              <UFormField label="Component Affected" class="col-span-2">
                <UInput v-model="form.component_affected" class="w-full" />
              </UFormField>
              <UFormField label="Planned">
                <UCheckbox v-model="form.planned" label="Planned downtime" />
              </UFormField>
              <UFormField label="Shift Asset">
                <UCheckbox v-model="form.shift_asset" label="Asset runs across multiple shifts" />
              </UFormField>
              <UFormField label="Repeat Failure">
                <UCheckbox v-model="form.repeat_failure" label="Repeat failure" />
              </UFormField>
              <UFormField label="Temporary Fix">
                <UCheckbox v-model="form.temporary_fix" label="Temporary fix applied" />
              </UFormField>
              <UFormField label="Details" class="col-span-2">
                <UTextarea v-model="form.details" :rows="2" class="w-full" />
              </UFormField>
              <UFormField label="Root Cause" class="col-span-2">
                <UTextarea v-model="form.root_cause" :rows="2" class="w-full" />
              </UFormField>
              <UFormField label="Corrective Action" class="col-span-2">
                <UTextarea v-model="form.corrective_action" :rows="2" class="w-full" />
              </UFormField>
            </div>

            <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="mt-4" />
          </div>

          <!-- Exacerbating factors ─ needs the downtime's id, so only once it exists -->
          <div v-show="modalTab === 'factors'" class="flex-1 overflow-y-auto px-6 py-5">
            <div v-if="!isEditing" class="py-8 text-center text-sm text-slate-400 dark:text-slate-500">
              Save this downtime record first to add exacerbating factors.
            </div>
            <div v-else class="rounded-lg border border-slate-200 dark:border-slate-700">
              <div class="border-b border-slate-100 dark:border-slate-800 px-4 py-3">
                <h4 class="text-sm font-semibold text-slate-800 dark:text-slate-100">Exacerbating Factors</h4>
                <p class="text-xs text-slate-500 dark:text-slate-400">Delays outside hands-on repair time — parts, supplier holds, approvals.</p>
              </div>

              <ul v-if="factors.length" class="divide-y divide-slate-100 dark:divide-slate-800">
                <li v-for="f in sortedFactors" :key="f.id" class="flex items-start gap-3 px-4 py-2.5 text-sm">
                  <div class="min-w-0 flex-1">
                    <div class="flex flex-wrap items-center gap-2">
                      <span class="font-medium text-slate-800 dark:text-slate-100">{{ factorTypeMap[f.factor_type_id] ?? 'Uncategorised' }}</span>
                      <span v-if="f.delay_hours != null" class="text-xs font-semibold text-orange-600 dark:text-orange-400">+{{ f.delay_hours.toFixed(1) }}h</span>
                      <span v-if="f.resolved" class="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium bg-green-50 text-green-600 ring-1 ring-green-200 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/30">Resolved</span>
                      <span v-else class="inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium bg-amber-50 text-amber-600 ring-1 ring-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-500/30">Ongoing</span>
                    </div>
                    <p v-if="f.start_date || f.end_date" class="text-[11px] text-slate-400 dark:text-slate-500">
                      {{ formatDate(f.start_date) }}{{ f.start_time ? ' ' + f.start_time.slice(0, 5) : '' }}
                      →
                      {{ f.end_date ? formatDate(f.end_date) + (f.end_time ? ' ' + f.end_time.slice(0, 5) : '') : 'ongoing' }}
                    </p>
                    <p v-if="f.notes" class="text-xs text-slate-500 dark:text-slate-400">{{ f.notes }}</p>
                  </div>
                  <div class="flex shrink-0 items-center gap-1">
                    <UButton variant="ghost" size="xs" icon="i-heroicons-pencil-square" color="neutral" @click="startEditFactor(f)" />
                    <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteFactor(f.id!)" />
                  </div>
                </li>
              </ul>
              <p v-else class="px-4 py-3 text-xs text-slate-400 dark:text-slate-500">No exacerbating factors recorded.</p>

              <!-- Add / edit factor form -->
              <div class="border-t border-slate-100 dark:border-slate-800 px-4 py-3">
                <div class="grid grid-cols-2 gap-x-4 gap-y-3">
                  <UFormField label="Factor" class="col-span-2">
                    <USelect v-model="factorDraft.factor_type_id" :items="factorTypeOptions" placeholder="Select factor" class="w-full" />
                  </UFormField>
                  <UFormField label="Start Date">
                    <UInput v-model="factorDraft.start_date" type="date" class="w-full" />
                  </UFormField>
                  <UFormField label="Start Time">
                    <UInput v-model="factorDraft.start_time" type="time" class="w-full" />
                  </UFormField>
                  <UFormField label="End Date">
                    <UInput v-model="factorDraft.end_date" type="date" class="w-full" />
                  </UFormField>
                  <UFormField label="End Time">
                    <UInput v-model="factorDraft.end_time" type="time" class="w-full" />
                  </UFormField>
                  <UFormField label="Delay Hours" :hint="factorAutoCalc ? 'Auto-calculated' : 'Manual'">
                    <UInput
                      v-model.number="factorDraft.delay_hours"
                      type="number"
                      step="0.25"
                      :disabled="factorAutoCalc"
                      :placeholder="factorAutoCalc ? 'From window on save' : 'e.g. 24'"
                      class="w-full"
                    />
                  </UFormField>
                  <UFormField label="Resolved">
                    <UCheckbox v-model="factorDraft.resolved" label="Factor resolved" />
                  </UFormField>
                  <UFormField label="Notes" class="col-span-2">
                    <UTextarea v-model="factorDraft.notes" :rows="2" placeholder="e.g. bearing on 3-week back-order from OEM; supplier account on stop-credit" class="w-full" />
                  </UFormField>
                </div>
                <p class="mt-2 text-[11px] text-slate-400 dark:text-slate-500">
                  Enter a start date &amp; time (and end, or leave open) to calculate delay hours across production shifts and holidays. Without a start time, type the hours manually.
                </p>
                <UAlert v-if="factorError" color="error" variant="soft" :description="factorError" class="mt-3" />
                <div class="mt-3 flex justify-end gap-2">
                  <UButton v-if="editingFactorId" variant="ghost" size="xs" color="neutral" @click="resetFactorDraft">Cancel edit</UButton>
                  <UButton size="xs" :loading="savingFactor" :disabled="!factorDraft.factor_type_id" @click="submitFactor">
                    {{ editingFactorId ? "Update Factor" : "Add Factor" }}
                  </UButton>
                </div>
              </div>
            </div>
          </div>

          <div class="flex shrink-0 justify-end gap-3 border-t border-slate-100 dark:border-slate-800 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
            <UButton :loading="saving" @click="save">{{ isEditing ? "Save Changes" : "Log Downtime" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Downtime Record</h3></template>
          <p class="text-sm text-slate-500 dark:text-slate-400">Delete downtime record <strong>#{{ deleteTarget?.downtime_id }}</strong>? This cannot be undone.</p>
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
