<script setup lang="ts">
import type { AssetPM, PmTask, WorkOrder } from "~/types"

const { isAdmin } = useAuth()
const { getAllPMs, getPM, createPM, updatePM, removePM, getPlans, getTasksByPlan } = useMaintenance()
const { getAll: getAssets } = useAssets()
const { create: createWorkOrder } = useWorkOrders()

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

const assetOptions = computed(() => [...(assets.value ?? [])].sort((a, b) => a.asset_id.localeCompare(b.asset_id)).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id })))
const planOptions = computed(() => (plans.value ?? []).map((p) => ({ label: `${p.pm_id} — ${p.description ?? p.frequency}`, value: p.pm_id })))

const planDescription = (planId?: string) =>
  (plans.value ?? []).find((p) => p.pm_id === planId)?.description ?? ""

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
const modalTab = ref<"details" | "tasks">("details")

const defaultForm = (): Partial<AssetPM> => ({ active: true })
const form = ref<Partial<AssetPM>>(defaultForm())

// ── Read-only task checklist for the selected PM plan ─────────
const pmTasks = ref<PmTask[]>([])
const loadingTasks = ref(false)

watch(() => form.value.pm_plan_id, async (planId) => {
  if (!planId) {
    pmTasks.value = []
    return
  }
  loadingTasks.value = true
  try {
    pmTasks.value = await getTasksByPlan(planId)
  } catch {
    pmTasks.value = []
  } finally {
    loadingTasks.value = false
  }
})

function openCreate() {
  form.value = defaultForm()
  isEditing.value = false
  editId.value = null
  formError.value = null
  modalTab.value = "details"
  showModal.value = true
}

async function openEdit(id: number) {
  form.value = { ...await getPM(id) }
  isEditing.value = true
  editId.value = id
  formError.value = null
  modalTab.value = "details"
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

// ── Create Work Order from PM ────────────────────────────────
const showWoModal = ref(false)
const woForm = ref<Partial<WorkOrder>>({})
const savingWo = ref(false)
const woError = ref<string | null>(null)
const woTypeOptions = ["corrective", "predictive", "preventative", "inspection", "project"]
const woPriorityOptions = ["Low", "Medium", "High"]

function openCreateWorkOrder() {
  woForm.value = {
    asset_id: form.value.asset_id,
    asset_pm_id: editId.value ?? undefined,
    typ: "preventative",
    planned: true,
    priority: "Medium",
    status: "requested",
    issue_date: new Date().toISOString().slice(0, 10),
    expected_date: form.value.next_service,
    description: planDescription(form.value.pm_plan_id),
    notes: `From PM schedule ${form.value.pm_plan_id ?? ""}`.trim(),
  }
  woError.value = null
  showModal.value = false // close PM modal, matches work-orders/index.vue onCreateOpen
  showWoModal.value = true
}

async function submitCreateWorkOrder() {
  savingWo.value = true
  woError.value = null
  try {
    await createWorkOrder(woForm.value as WorkOrder)
    showWoModal.value = false
    await navigateTo("/work-orders") // no toast system in app; land on the new WO's list
  } catch (e: unknown) {
    woError.value = (e as { message?: string }).message ?? "Failed to create work order"
  } finally {
    savingWo.value = false
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

          <div class="flex gap-2 border-b border-slate-100 dark:border-slate-800 px-6">
            <button
              v-for="t in [{ label: 'Details', value: 'details' }, { label: `Tasks${pmTasks.length ? ` (${pmTasks.length})` : ''}`, value: 'tasks' }]"
              :key="t.value"
              type="button"
              class="border-b-2 px-1 py-2.5 text-sm font-medium transition-colors"
              :class="modalTab === t.value ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'"
              @click="modalTab = t.value as 'details' | 'tasks'"
            >
              {{ t.label }}
            </button>
          </div>

          <div v-show="modalTab === 'details'" class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
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

          <div v-show="modalTab === 'tasks'" class="px-6 py-5">
            <p class="mb-3 text-xs text-slate-500 dark:text-slate-400">
              Checklist from the selected PM plan. Edit tasks in Settings &rsaquo; PM Plans.
            </p>
            <div v-if="!form.pm_plan_id" class="py-8 text-center text-sm text-slate-400 dark:text-slate-500">
              Select a PM plan on the Details tab to see its tasks.
            </div>
            <div v-else-if="loadingTasks" class="py-8 text-center text-sm text-slate-400 dark:text-slate-500">Loading…</div>
            <ul v-else-if="pmTasks.length" class="divide-y divide-slate-100 dark:divide-slate-800">
              <li v-for="t in pmTasks" :key="t.id" class="flex items-start gap-2 py-2 text-sm text-slate-700 dark:text-slate-200">
                <UIcon name="i-heroicons-check-circle" class="mt-0.5 h-4 w-4 shrink-0 text-slate-300 dark:text-slate-600" />
                <span>{{ t.task }}</span>
              </li>
            </ul>
            <p v-else class="py-8 text-center text-sm text-slate-400 dark:text-slate-500">No tasks defined for this PM plan.</p>
          </div>

          <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="mx-6 mb-4" />
          <div class="flex justify-between gap-3 border-t border-slate-100 dark:border-slate-800 px-6 py-4">
            <UButton
              v-if="isEditing && form.asset_id"
              variant="outline"
              leading-icon="i-heroicons-clipboard-document-list"
              @click="openCreateWorkOrder"
            >Create Work Order</UButton>
            <div class="flex gap-3 ml-auto">
              <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
              <UButton :loading="saving" @click="save">{{ isEditing ? "Save Changes" : "Create Schedule" }}</UButton>
            </div>
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

    <!-- Create Work Order Modal -->
    <UModal v-model:open="showWoModal" :ui="{ content: 'max-w-2xl' }">
      <template #content>
        <div class="flex max-h-[90vh] w-full flex-col rounded-xl bg-white shadow-xl dark:bg-slate-900">
          <div class="flex shrink-0 items-start gap-4 border-b border-slate-100 dark:border-slate-800 px-6 py-5">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 dark:bg-blue-500/10">
              <UIcon name="i-heroicons-clipboard-document-list" class="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">Create Work Order</h3>
              <p class="text-sm text-slate-500 dark:text-slate-400">PM {{ woForm.asset_pm_id }} — {{ woForm.asset_id }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showWoModal = false" />
          </div>
          <div class="flex-1 overflow-y-auto px-6 py-5">
            <div class="grid grid-cols-2 gap-x-5 gap-y-4">
              <UFormField label="Asset">
                <UInput :model-value="woForm.asset_id" readonly class="w-full" />
              </UFormField>
              <UFormField label="Priority">
                <USelect v-model="woForm.priority" :items="woPriorityOptions" class="w-full" />
              </UFormField>
              <UFormField label="Type">
                <USelect v-model="woForm.typ" :items="woTypeOptions" class="w-full" />
              </UFormField>
              <UFormField label="Planned">
                <USelect v-model="woForm.planned" :items="[{ label: 'Planned', value: true }, { label: 'Unplanned', value: false }]" class="w-full" />
              </UFormField>
              <UFormField label="Issue Date">
                <UInput v-model="woForm.issue_date" type="date" class="w-full" />
              </UFormField>
              <UFormField label="Expected Date">
                <UInput v-model="woForm.expected_date" type="date" class="w-full" />
              </UFormField>
              <UFormField label="Estimated Hours">
                <UInput v-model.number="woForm.estimated_hours" type="number" step="0.5" class="w-full" />
              </UFormField>
              <UFormField label="Description" class="col-span-2">
                <UTextarea v-model="woForm.description" :rows="3" class="w-full" />
              </UFormField>
              <UFormField label="Notes" class="col-span-2">
                <UTextarea v-model="woForm.notes" :rows="2" class="w-full" />
              </UFormField>
            </div>
            <UAlert v-if="woError" color="error" variant="soft" :description="woError" class="mt-4" />
          </div>
          <div class="flex shrink-0 justify-end gap-3 border-t border-slate-100 dark:border-slate-800 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showWoModal = false">Cancel</UButton>
            <UButton :loading="savingWo" leading-icon="i-heroicons-check" @click="submitCreateWorkOrder">
              Create Work Order
            </UButton>
          </div>
        </div>
      </template>
    </UModal>
  </div>
</template>
