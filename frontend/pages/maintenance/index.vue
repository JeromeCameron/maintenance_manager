<script setup lang="ts">
import type { AssetPM } from "~/types"

const { isAdmin } = useAuth()
const { getAllPMs, getPM, createPM, updatePM, removePM, getPlans } = useMaintenance()
const { getAll: getAssets } = useAssets()

const { data: assetPMs, refresh } = await useAsyncData("asset-pms", () => getAllPMs())
const { data: plans } = await useAsyncData("pm-plans", () => getPlans())
const { data: assets } = await useAsyncData("assets-select", () => getAssets())

const planMap = computed(() => {
  const m: Record<string, string> = {}
  for (const p of plans.value ?? []) m[p.pm_id] = p.description ?? p.pm_id
  return m
})

const today = new Date()
const in30Days = new Date(today)
in30Days.setDate(today.getDate() + 30)

const pmsDueSoon = computed(() =>
  (assetPMs.value ?? []).filter((pm) => pm.next_service && new Date(pm.next_service) <= in30Days && pm.active)
)

const assetOptions = computed(() => (assets.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id })))
const planOptions = computed(() => (plans.value ?? []).map((p) => ({ label: `${p.pm_id} — ${p.description ?? p.frequency}`, value: p.pm_id })))

const activeTab = ref("all")
const tabs = [
  { label: "All PMs", value: "all" },
  { label: `Due Soon (${pmsDueSoon.value.length})`, value: "due" },
  { label: "PM Plans", value: "plans" },
]

function byNextService(a: AssetPM, b: AssetPM) {
  if (!a.next_service && !b.next_service) return 0
  if (!a.next_service) return 1
  if (!b.next_service) return -1
  return a.next_service.localeCompare(b.next_service)
}

const filtered = computed(() => {
  const list = activeTab.value === "due" ? pmsDueSoon.value : assetPMs.value ?? []
  return [...list].sort(byNextService)
})

// ── Form modal ───────────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)

const defaultForm = (): Partial<AssetPM> => ({ active: true })
const form = ref<Partial<AssetPM>>(defaultForm())

function openCreate() {
  form.value = defaultForm()
  isEditing.value = false
  editId.value = null
  formError.value = null
  showModal.value = true
}

async function openEdit(id: number) {
  form.value = { ...await getPM(id) }
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
      await updatePM(editId.value, form.value as AssetPM)
    } else {
      await createPM(form.value as AssetPM)
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
const deleteTarget = ref<AssetPM | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value?.id) return
  deleting.value = true
  try {
    await removePM(deleteTarget.value.id)
    await refresh()
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="flex min-h-full flex-col gap-4">
    <UAlert v-if="pmsDueSoon.length" color="warning" variant="soft" icon="i-heroicons-clock"
      :title="`${pmsDueSoon.length} PM${pmsDueSoon.length > 1 ? 's' : ''} due in the next 30 days`" />

    <div class="flex gap-2 border-b border-slate-200 dark:border-slate-700">
      <button v-for="tab in tabs" :key="tab.value"
        class="border-b-2 px-4 py-2 text-sm font-medium transition-colors"
        :class="activeTab === tab.value ? 'border-primary-500 text-primary-600' : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'"
        @click="activeTab = tab.value">
        {{ tab.label }}
      </button>
    </div>

    <UCard v-if="activeTab !== 'plans'" :ui="{ root: 'flex flex-col flex-1 min-h-0', body: 'flex flex-col flex-1 min-h-0 p-0' }">
      <template #header>
        <div class="flex justify-end">
          <UButton leading-icon="i-heroicons-plus" @click="openCreate" class="!bg-blue-700 hover:!bg-blue-800">New PM Schedule</UButton>
        </div>
      </template>

      <!-- PM schedule card list -->
      <div class="overflow-auto h-full p-4 space-y-2">
        <div v-if="filtered.length === 0" class="py-12 text-center text-sm text-gray-400 dark:text-slate-500">
          No PM schedules found.
        </div>
        <div
          v-for="pm in filtered"
          :key="pm.id"
          class="flex cursor-pointer items-start gap-4 rounded-lg px-5 py-4 ring-1 ring-gray-200 dark:ring-slate-700 hover:bg-blue-50/40 dark:hover:bg-blue-500/10 transition-colors border-l-4"
          :class="pm.next_service && new Date(pm.next_service) <= in30Days && pm.active ? 'border-l-amber-400' : 'border-l-transparent'"
          @click="openEdit(pm.id!)"
        >
          <!-- Left icon -->
          <div class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gray-100 dark:bg-slate-800">
            <UIcon name="i-heroicons-calendar-days" class="h-4 w-4 text-gray-400 dark:text-slate-500" />
          </div>

          <!-- Main content -->
          <div class="min-w-0 flex-1">
            <!-- Title -->
            <div class="flex items-center gap-2">
              <span class="text-sm font-semibold text-slate-800 dark:text-slate-100">{{ pm.asset_id }}</span>
            </div>
            <!-- PM Plan -->
            <p class="mt-0.5 truncate text-xs text-gray-500 dark:text-slate-400" :title="planMap[pm.pm_plan_id] ?? pm.pm_plan_id">
              {{ planMap[pm.pm_plan_id] ?? pm.pm_plan_id ?? "—" }}
            </p>
            <!-- Meta row -->
            <div class="mt-1.5 flex flex-wrap items-center gap-2">
              <span v-if="pm.last_service" class="flex items-center gap-1 text-[11px] text-gray-400 dark:text-slate-500">
                <UIcon name="i-heroicons-check" class="h-3 w-3" />
                Last {{ pm.last_service }}
              </span>
              <span
                v-if="pm.next_service"
                class="flex items-center gap-1 text-[11px]"
                :class="new Date(pm.next_service) <= in30Days ? 'font-semibold text-amber-600' : 'text-gray-400 dark:text-slate-500'"
              >
                <UIcon name="i-heroicons-calendar" class="h-3 w-3" />
                Next {{ pm.next_service }}
              </span>
            </div>
          </div>

          <!-- Right side -->
          <div class="shrink-0 flex flex-col items-end gap-2">
            <UBadge :color="pm.active ? 'success' : 'neutral'" variant="soft" size="xs">{{ pm.active ? "Active" : "Inactive" }}</UBadge>
            <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click.stop="deleteTarget = pm" />
          </div>
        </div>
      </div>
    </UCard>

    <UCard v-else>
      <UTable :data="plans ?? []" :ui="{ th: 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 font-semibold', tr: 'odd:bg-white dark:odd:bg-slate-900 even:bg-slate-50 dark:even:bg-slate-800 hover:bg-blue-50 dark:hover:bg-blue-500/10 transition-colors' }" :columns="[
        { accessorKey: 'pm_id', header: 'Plan ID' },
        { accessorKey: 'asset_type', header: 'Asset Type' },
        { accessorKey: 'trigger', header: 'Trigger' },
        { accessorKey: 'frequency', header: 'Frequency' },
        { accessorKey: 'owner', header: 'Owner' },
        { accessorKey: 'description', header: 'Description' },
      ]" />
    </UCard>

    <!-- Create / Edit Modal -->
    <UModal v-model:open="showModal">
      <template #content>
        <div class="w-full max-w-lg rounded-xl bg-white shadow-xl dark:bg-slate-900">
          <div class="flex items-start gap-4 border-b border-slate-100 dark:border-slate-800 px-6 py-5">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 dark:bg-blue-500/10">
              <UIcon name="i-heroicons-calendar-days" class="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">{{ isEditing ? "Edit PM Schedule" : "New PM Schedule" }}</h3>
              <p class="text-sm text-slate-500 dark:text-slate-400">{{ isEditing ? "Update PM schedule" : "Schedule preventative maintenance" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>
          <div class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
            <UFormField label="Asset" required class="col-span-2">
              <USelect v-model="form.asset_id" :items="assetOptions" placeholder="Select asset" class="w-full" />
            </UFormField>
            <UFormField label="PM Plan" required class="col-span-2">
              <USelect v-model="form.pm_plan_id" :items="planOptions" placeholder="Select plan" class="w-full" />
            </UFormField>
            <UFormField label="Last Service Date">
              <UInput v-model="form.last_service" type="date" class="w-full" />
            </UFormField>
            <UFormField label="Next Service Date">
              <UInput v-model="form.next_service" type="date" class="w-full" />
            </UFormField>
            <UFormField label="Active" class="col-span-2">
              <UCheckbox v-model="form.active" label="Schedule is active" />
            </UFormField>
          </div>
          <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 dark:border-slate-800 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
            <UButton :loading="saving" @click="save">{{ isEditing ? "Save Changes" : "Create Schedule" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete PM Schedule</h3></template>
          <p class="text-sm text-slate-500 dark:text-slate-400">Delete PM schedule <strong>#{{ deleteTarget?.id }}</strong>? This cannot be undone.</p>
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
