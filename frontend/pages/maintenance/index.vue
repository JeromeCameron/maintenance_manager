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

const columns = [
  { accessorKey: "id", header: "ID" },
  { accessorKey: "asset_id", header: "Asset" },
  { accessorKey: "pm_plan_id", header: "PM Plan" },
  { accessorKey: "last_service", header: "Last Service" },
  { accessorKey: "next_service", header: "Next Service" },
  { accessorKey: "active", header: "Active" },
  { id: "actions", header: "" },
]

const filtered = computed(() => activeTab.value === "due" ? pmsDueSoon.value : assetPMs.value ?? [])

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
  <div class="space-y-4">
    <UAlert v-if="pmsDueSoon.length" color="warning" variant="soft" icon="i-heroicons-clock"
      :title="`${pmsDueSoon.length} PM${pmsDueSoon.length > 1 ? 's' : ''} due in the next 30 days`" />

    <div class="flex gap-2 border-b border-slate-200">
      <button v-for="tab in tabs" :key="tab.value"
        class="border-b-2 px-4 py-2 text-sm font-medium transition-colors"
        :class="activeTab === tab.value ? 'border-primary-500 text-primary-600' : 'border-transparent text-slate-500 hover:text-slate-700'"
        @click="activeTab = tab.value">
        {{ tab.label }}
      </button>
    </div>

    <UCard v-if="activeTab !== 'plans'">
      <template #header>
        <div class="flex justify-end">
          <UButton leading-icon="i-heroicons-plus" @click="openCreate" class="!bg-blue-700 hover:!bg-blue-800">New PM Schedule</UButton>
        </div>
      </template>
      <UTable :data="filtered" :columns="columns" :ui="{ th: 'bg-slate-100 text-slate-500 font-semibold', tr: 'odd:bg-white even:bg-slate-50 hover:bg-blue-50 transition-colors' }">
        <template #asset_id-cell="{ row: { original: row } }">
          <span class="font-medium text-slate-700">{{ row.asset_id }}</span>
        </template>
        <template #pm_plan_id-cell="{ row: { original: row } }">
          <span class="block max-w-[180px] truncate" :title="planMap[row.pm_plan_id] ?? row.pm_plan_id">
            {{ planMap[row.pm_plan_id] ?? row.pm_plan_id ?? "—" }}
          </span>
        </template>
        <template #active-cell="{ row: { original: row } }">
          <UBadge :color="row.active ? 'success' : 'neutral'" variant="soft" size="sm">{{ row.active ? "Active" : "Inactive" }}</UBadge>
        </template>
        <template #next_service-cell="{ row: { original: row } }">
          <span :class="row.next_service && new Date(row.next_service) <= in30Days ? 'font-semibold text-amber-600' : ''">
            {{ row.next_service ?? "—" }}
          </span>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-eye" @click="openEdit(row.id)" />
            <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <UCard v-else>
      <UTable :data="plans ?? []" :ui="{ th: 'bg-slate-100 text-slate-500 font-semibold', tr: 'odd:bg-white even:bg-slate-50 hover:bg-blue-50 transition-colors' }" :columns="[
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
        <div class="w-full max-w-lg rounded-xl bg-white shadow-xl">
          <div class="flex items-start gap-4 border-b border-slate-100 px-6 py-5">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50">
              <UIcon name="i-heroicons-calendar-days" class="h-5 w-5 text-blue-600" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900">{{ isEditing ? "Edit PM Schedule" : "New PM Schedule" }}</h3>
              <p class="text-sm text-slate-500">{{ isEditing ? "Update PM schedule" : "Schedule preventative maintenance" }}</p>
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
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
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
          <p class="text-sm text-slate-500">Delete PM schedule <strong>#{{ deleteTarget?.id }}</strong>? This cannot be undone.</p>
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
