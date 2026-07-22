<script setup lang="ts">
import type { Downtime } from "~/types"

const { isAdmin } = useAuth()
const { getAll, getOne, create, update, remove, getCauses } = useDowntime()
const { getAll: getAssets } = useAssets()
const { getAll: getWorkOrders } = useWorkOrders()

const { data: downtimes, refresh } = await useAsyncData("downtimes", () => getAll())
const { data: causes } = await useAsyncData("downtime-causes", () => getCauses())
const { data: assets } = await useAsyncData("assets-select", () => getAssets())
const { data: workOrders } = await useAsyncData("downtime-work-orders", () => getWorkOrders())

const causeMap = computed(() => {
  const m: Record<number, string> = {}
  for (const c of causes.value ?? []) { if (c.cause_id != null) m[c.cause_id] = c.name }
  return m
})

const causeOptions = computed(() => (causes.value ?? []).map((c) => ({ label: c.name, value: c.cause_id })))
const assetOptions = computed(() => (assets.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id })))
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
    .sort((a, b) => new Date(b.start_date ?? "").getTime() - new Date(a.start_date ?? "").getTime())
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

const defaultForm = (): Partial<Downtime> => ({ planned: false, shift_asset: false })
const form = ref<Partial<Downtime>>(defaultForm())

function openCreate() {
  form.value = defaultForm()
  isEditing.value = false
  editId.value = null
  formError.value = null
  showModal.value = true
}

async function openEdit(id: number) {
  form.value = { ...await getOne(id) }
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
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>
          <div class="flex-1 overflow-y-auto px-6 py-5">
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
