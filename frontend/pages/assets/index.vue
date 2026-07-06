<script setup lang="ts">
import type { Asset, AssetModel, AssetScores, WorkOrder, Downtime, Inspection, Issue } from "~/types"

const { isAdmin } = useAuth()
const { getAll, getOne, create, update, remove, getScoreByAsset, createScore, updateScore, getWorkOrders, getDowntimes, getInspections, getAvailability30d } = useAssets()
const { getOne: getModelOne } = useAssetModels()
const { getByAsset: getIssuesByAsset } = useIssues()
const { getAll: getLocations } = useLocations()

const { data: assets, refresh } = await useAsyncData("assets", () => getAll())
const { data: locations } = await useAsyncData("locations-select", () => getLocations())

const statusColors: Record<string, string> = {
  operational: "success", maintenance: "warning", out_of_service: "error", disposed: "neutral", retired: "neutral",
}
const severityColors: Record<string, string> = { low: "success", medium: "warning", high: "error", critical: "error" }
const woStatusColors: Record<string, string> = { requested: "neutral", approved: "info", in_progress: "warning", completed: "success", cancelled: "neutral" }

const locationMap = computed(() => {
  const m: Record<number, string> = {}
  for (const l of locations.value ?? []) { if (l.location_id != null) m[l.location_id] = l.name }
  return m
})
const locationOptions = computed(() => (locations.value ?? []).map((l) => ({ label: l.name, value: l.location_id })))

const columns = [
  { accessorKey: "asset_id", header: "Asset ID" },
  { accessorKey: "manufacturer", header: "Manufacturer" },
  { accessorKey: "category", header: "Category" },
  { accessorKey: "status", header: "Status" },
  { accessorKey: "owned", header: "Ownership" },
  { accessorKey: "location_id", header: "Location" },
  { id: "actions", header: "" },
]

const statusOptions = ["operational", "maintenance", "out_of_service", "disposed", "retired"]
const categoryOptions = ["baler", "conveyor", "bobcat", "forklift", "scale"]
const ownershipOptions = ["owned", "rented", "leased"]

const validSubStatuses: Record<string, string[]> = {
  operational:    ["watch_list", "limited_duty", "pending_inspection"],
  maintenance:    ["in_repair", "awaiting_parts", "pending_inspection"],
  out_of_service: ["in_repair", "awaiting_parts", "pending_inspection"],
}
const subStatusOptions = computed(() => {
  const opts = (validSubStatuses[form.value.status ?? ""] ?? []).map((s) => ({ label: s.replace(/_/g, " "), value: s }))
  return [{ label: "None", value: null }, ...opts]
})

const search = ref("")
const filtered = computed(() =>
  (assets.value ?? []).filter((a) => {
    const q = search.value.toLowerCase()
    return !q || a.asset_id.toLowerCase().includes(q) || a.manufacturer.toLowerCase().includes(q)
  })
)

// ── Create modal (simple, no tabs) ───────────────────────────
const showCreateModal = ref(false)
const saving = ref(false)
const formError = ref<string | null>(null)
const defaultForm = (): Partial<Asset> => ({ status: "operational", owned: "owned", category: "baler" })
const form = ref<Partial<Asset>>(defaultForm())

function openCreate() {
  form.value = defaultForm()
  formError.value = null
  showCreateModal.value = true
}

async function saveCreate() {
  saving.value = true
  formError.value = null
  try {
    await create(form.value as Asset)
    await refresh()
    showCreateModal.value = false
  } catch (e: unknown) {
    formError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    saving.value = false
  }
}

// ── Criticality scoring reference ────────────────────────────
const scoreFields = [
  {
    key: "safety_score" as const,
    label: "Safety / Compliance",
    question: "Could failure cause injury, environmental harm, or regulatory breach?",
    max: 3,
    levels: [
      "No safety or compliance impact",
      "Minor safety risk, manageable",
      "Significant risk requiring controls",
      "Severe safety, environmental, or regulatory risk",
    ],
  },
  {
    key: "operational_score" as const,
    label: "Operational Impact",
    question: "Does failure stop or severely limit operations?",
    max: 3,
    levels: [
      "Minimal impact",
      "Reduced efficiency",
      "Partial operational stoppage",
      "Full operational stoppage",
    ],
  },
  {
    key: "backup_score" as const,
    label: "Backup Availability",
    question: "Is there a spare or workaround available?",
    max: 2,
    levels: [
      "Immediate backup available",
      "Limited or shared backup",
      "No backup available",
    ],
  },
  {
    key: "repair_score" as const,
    label: "Repair Complexity",
    question: "Is repair time long or requires specialised parts/skills?",
    max: 2,
    levels: [
      "Quick repair (< 4 hours)",
      "Moderate repair (same day)",
      "Long repair (multi-day / specialist required)",
    ],
  },
  {
    key: "usage_score" as const,
    label: "Equipment Usage",
    question: "How hard and how often is the equipment used?",
    max: 2,
    levels: [
      "Low — < 100 hrs/month",
      "Medium — 100–200 hrs/month",
      "High — > 200 hrs/month",
    ],
  },
]

function getCriticalityTier(total: number): { label: string; color: string } {
  if (total >= 10) return { label: "Critical", color: "text-red-600" }
  if (total >= 7)  return { label: "High",     color: "text-orange-500" }
  if (total >= 4)  return { label: "Medium",   color: "text-amber-500" }
  return              { label: "Low",      color: "text-green-600" }
}

function getRiskFlag(s: { usage_score?: number | null; operational_score?: number | null }): { label: string; color: string; bg: string } {
  const u = s.usage_score ?? 0
  const o = s.operational_score ?? 0
  if (u === 2 && o >= 2) return { label: "High Risk",   color: "text-red-700",    bg: "bg-red-50 border-red-200" }
  if (u >= 1 && o >= 1)  return { label: "Medium Risk", color: "text-amber-700",  bg: "bg-amber-50 border-amber-200" }
  return                         { label: "Low Risk",    color: "text-green-700",  bg: "bg-green-50 border-green-200" }
}

// ── View / Edit tabbed modal ─────────────────────────────────
const showViewModal = ref(false)
const activeTab = ref("details")
const loadingAsset = ref(false)

// Details tab
const editId = ref<string | null>(null)
const savingEdit = ref(false)
const editError = ref<string | null>(null)

// Related data
const modelData = ref<AssetModel | null>(null)
const scoresData = ref<AssetScores | null>(null)
const editingScores = ref(false)
const scoresForm = ref<Partial<AssetScores>>({})
const savingScores = ref(false)
const scoresError = ref<string | null>(null)

function openScoresEdit() {
  scoresForm.value = scoresData.value
    ? { ...scoresData.value }
    : { asset_id: editId.value ?? undefined }
  scoresError.value = null
  editingScores.value = true
}

async function saveScores() {
  if (!editId.value) return
  savingScores.value = true
  scoresError.value = null
  try {
    if (scoresData.value?.score_id) {
      scoresData.value = await updateScore(scoresData.value.score_id, scoresForm.value as AssetScores)
    } else {
      scoresData.value = await createScore({ ...scoresForm.value, asset_id: editId.value } as AssetScores)
    }
    editingScores.value = false
  } catch (e: unknown) {
    scoresError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingScores.value = false
  }
}
const workOrdersData = ref<WorkOrder[]>([])
const downtimeData = ref<Downtime[]>([])
const inspectionsData = ref<Inspection[]>([])
const issuesData = ref<Issue[]>([])
const availability30d = ref<number>(100)

const isBaler = computed(() => form.value.category === "baler")

const availabilityMTD = computed(() => availability30d.value)

const closedStatuses = ["completed", "cancelled", "closed"]
const openWorkOrders = computed(() => workOrdersData.value.filter((w) => !closedStatuses.includes(w.status)))
const recentWorkOrders = computed(() =>
  workOrdersData.value
    .filter((w) => closedStatuses.includes(w.status))
    .sort((a, b) => (b.issue_date ?? "").localeCompare(a.issue_date ?? ""))
    .slice(0, 10)
)

const tabs = computed(() => {
  const t: { label: string; value: string }[] = [{ label: "Details", value: "details" }]
  if (isBaler.value) t.push({ label: "Baler Info", value: "baler" })
  t.push({ label: "Scores", value: "scores" })
  if (openWorkOrders.value.length) t.push({ label: "Open Work Orders", value: "open-wo" })
  t.push(
    { label: "Recent Work Orders", value: "recent-wo" },
    { label: "Downtime", value: "downtime" },
    { label: "Inspections", value: "inspections" },
    { label: "Issues", value: "issues" },
  )
  return t
})

async function openAsset(id: string) {
  loadingAsset.value = true
  activeTab.value = "details"
  editId.value = id
  editError.value = null
  editingScores.value = false
  showViewModal.value = true

  const asset = await getOne(id)
  form.value = { ...asset }

  const [scores, wos, downtimes, inspections, issues, model, avail] = await Promise.all([
    getScoreByAsset(id).catch(() => null),
    getWorkOrders(id).catch(() => []),
    getDowntimes(id).catch(() => []),
    getInspections(id).catch(() => []),
    getIssuesByAsset(id).catch(() => []),
    (asset.category === "baler" && asset.model_no) ? getModelOne(asset.model_no).catch(() => null) : Promise.resolve(null),
    getAvailability30d(id).catch(() => null),
  ])

  modelData.value = model
  scoresData.value = scores
  workOrdersData.value = wos ?? []
  downtimeData.value = downtimes ?? []
  inspectionsData.value = inspections ?? []
  issuesData.value = issues ?? []
  availability30d.value = avail?.availability ?? 100
  loadingAsset.value = false
}

async function saveEdit() {
  if (!editId.value) return
  savingEdit.value = true
  editError.value = null
  try {
    await update(editId.value, form.value as Asset)
    await refresh()
    showViewModal.value = false
  } catch (e: unknown) {
    editError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingEdit.value = false
  }
}

// ── Delete modal ─────────────────────────────────────────────
const deleteTarget = ref<Asset | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.asset_id)
    await refresh()
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}

function parseDateLocal(v: string): Date {
  const [y, m, d] = v.slice(0, 10).split("-").map(Number)
  return new Date(y, m - 1, d)
}
function fmtDate(v?: string | null) { return v ? parseDateLocal(v).toLocaleDateString() : "—" }
function fmtDateShort(v?: string | null) {
  if (!v) return "—"
  return parseDateLocal(v).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "2-digit" })
}
</script>

<template>
  <div class="space-y-4">
    <UCard>
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <UInput v-model="search" placeholder="Search by ID or manufacturer..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
          <UButton leading-icon="i-heroicons-plus" @click="openCreate" class="!bg-blue-700 hover:!bg-blue-800">New Asset</UButton>
        </div>
      </template>
      <UTable
        :data="filtered"
        :columns="columns"
        :ui="{
          root: 'relative overflow-auto max-h-[calc(100vh-22rem)]',
          th: 'bg-slate-100 text-slate-500 font-semibold',
          tr: 'odd:bg-white even:bg-slate-50 hover:bg-blue-50 transition-colors',
        }"
      >
        <template #status-cell="{ row: { original: row } }">
          <UBadge :color="statusColors[row.status] ?? 'neutral'" variant="soft">{{ row.status.replace(/_/g, " ") }}</UBadge>
        </template>
        <template #category-cell="{ row: { original: row } }">
          <span class="capitalize">{{ row.category }}</span>
        </template>
        <template #owned-cell="{ row: { original: row } }">
          <span class="capitalize">{{ row.owned }}</span>
        </template>
        <template #location_id-cell="{ row: { original: row } }">
          {{ row.location_id ? locationMap[row.location_id] ?? row.location_id : "—" }}
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-eye" @click="openAsset(row.asset_id)" />
            <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Create Modal -->
    <UModal v-model:open="showCreateModal">
      <template #content>
        <div class="w-full max-w-2xl rounded-xl bg-white shadow-xl">
          <div class="flex items-start gap-4 border-b border-slate-100 px-6 py-5">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50">
              <UIcon name="i-heroicons-wrench-screwdriver" class="h-5 w-5 text-blue-600" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900">New Asset</h3>
              <p class="text-sm text-slate-500">Register a new asset</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showCreateModal = false" />
          </div>
          <div class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
            <UFormField label="Asset ID" required>
              <UInput v-model="form.asset_id" placeholder="e.g. BAL-001" class="w-full" />
            </UFormField>
            <UFormField label="Manufacturer" required>
              <UInput v-model="form.manufacturer" placeholder="e.g. Caterpillar" class="w-full" />
            </UFormField>
            <UFormField label="Alias">
              <UInput v-model="form.alias" placeholder="e.g. Big Blue Baler" class="w-full" />
            </UFormField>
            <UFormField label="Category">
              <USelect v-model="form.category" :items="categoryOptions" class="w-full" />
            </UFormField>
            <UFormField label="Status">
              <USelect v-model="form.status" :items="statusOptions" class="w-full" @update:model-value="form.sub_status = null" />
            </UFormField>
            <UFormField label="Sub-status">
              <USelect v-model="form.sub_status" :items="subStatusOptions" :disabled="!form.status || form.status === 'disposed'" placeholder="None" class="w-full" />
            </UFormField>
            <UFormField label="Ownership">
              <USelect v-model="form.owned" :items="ownershipOptions" class="w-full" />
            </UFormField>
            <UFormField label="Location">
              <USelect v-model="form.location_id" :items="locationOptions" placeholder="Select location" class="w-full" />
            </UFormField>
            <UFormField label="Model No.">
              <UInput v-model="form.model_no" class="w-full" />
            </UFormField>
            <UFormField label="Serial No.">
              <UInput v-model="form.serial_no" class="w-full" />
            </UFormField>
            <UFormField label="Year">
              <UInput v-model.number="form.yr" type="number" class="w-full" />
            </UFormField>
            <UFormField label="Date In Service">
              <UInput v-model="form.date_in_service" type="date" class="w-full" />
            </UFormField>
            <UFormField label="Notes" class="col-span-2">
              <UTextarea v-model="form.notes" :rows="3" class="w-full" />
            </UFormField>
          </div>
          <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showCreateModal = false">Cancel</UButton>
            <UButton :loading="saving" @click="saveCreate">Create Asset</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- View / Edit tabbed modal -->
    <UModal v-model:open="showViewModal" :ui="{ content: 'max-w-4xl' }">
      <template #content>
        <div class="flex h-[85vh] w-full flex-col rounded-xl bg-white shadow-xl">

          <!-- Header -->
          <div class="flex shrink-0 items-center gap-4 border-b border-slate-100 px-6 py-4">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50">
              <UIcon name="i-heroicons-wrench-screwdriver" class="h-5 w-5 text-blue-600" />
            </div>
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <span class="text-base font-semibold text-slate-900">{{ form.asset_id }}</span>
                <span v-if="form.alias" class="text-sm text-slate-400">· {{ form.alias }}</span>
                <UBadge v-if="form.status" :color="statusColors[form.status] ?? 'neutral'" variant="soft" size="xs" class="capitalize">{{ form.status?.replace(/_/g, " ") }}</UBadge>
              </div>
              <p class="text-xs text-slate-400">{{ form.manufacturer }}<span v-if="form.model_no"> · {{ form.model_no }}</span></p>
            </div>
            <div
              v-if="!loadingAsset"
              class="flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold"
              :style="availabilityMTD >= 90 ? 'background:#f0fdf4;color:#15803d' : availabilityMTD >= 75 ? 'background:#fffbeb;color:#b45309' : 'background:#fef2f2;color:#b91c1c'"
            >
              <span
                class="h-2 w-2 rounded-full"
                :style="availabilityMTD >= 90 ? 'background:#22c55e' : availabilityMTD >= 75 ? 'background:#f59e0b' : 'background:#ef4444'"
              />
              {{ availabilityMTD.toFixed(1) }}% 30d Avail.
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showViewModal = false" />
          </div>

          <!-- Loading -->
          <div v-if="loadingAsset" class="flex flex-1 items-center justify-center">
            <UIcon name="i-heroicons-arrow-path" class="h-6 w-6 animate-spin text-slate-400" />
          </div>

          <template v-else>
            <!-- Custom tab bar -->
            <div class="flex shrink-0 gap-1 overflow-x-auto border-b border-slate-100 px-6">
              <button
                v-for="tab in tabs" :key="tab.value"
                @click="activeTab = tab.value"
                class="whitespace-nowrap border-b-2 px-3 py-3 text-sm font-medium transition-colors"
                :class="activeTab === tab.value
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'"
              >{{ tab.label }}</button>
            </div>

            <!-- Tab content (scrollable, fills remaining space) -->
            <div class="min-h-0 flex-1 overflow-y-auto">

              <!-- Details -->
              <div v-if="activeTab === 'details'" class="px-6 py-5">
                <div class="grid grid-cols-2 gap-x-5 gap-y-4">
                  <UFormField label="Asset ID" required>
                    <UInput v-model="form.asset_id" disabled class="w-full" />
                  </UFormField>
                  <UFormField label="Manufacturer" required>
                    <UInput v-model="form.manufacturer" class="w-full" />
                  </UFormField>
                  <UFormField label="Alias">
                    <UInput v-model="form.alias" placeholder="e.g. Big Blue Baler" class="w-full" />
                  </UFormField>
                  <UFormField label="Category">
                    <USelect v-model="form.category" :items="categoryOptions" class="w-full" />
                  </UFormField>
                  <UFormField label="Status">
                    <USelect v-model="form.status" :items="statusOptions" class="w-full" @update:model-value="form.sub_status = null" />
                  </UFormField>
                  <UFormField label="Sub-status">
                    <USelect v-model="form.sub_status" :items="subStatusOptions" :disabled="!form.status || form.status === 'disposed'" placeholder="None" class="w-full" />
                  </UFormField>
                  <UFormField label="Ownership">
                    <USelect v-model="form.owned" :items="ownershipOptions" class="w-full" />
                  </UFormField>
                  <UFormField label="Location">
                    <USelect v-model="form.location_id" :items="locationOptions" placeholder="Select location" class="w-full" />
                  </UFormField>
                  <UFormField label="Model No.">
                    <UInput v-model="form.model_no" class="w-full" />
                  </UFormField>
                  <UFormField label="Serial No.">
                    <UInput v-model="form.serial_no" class="w-full" />
                  </UFormField>
                  <UFormField label="Year">
                    <UInput v-model.number="form.yr" type="number" class="w-full" />
                  </UFormField>
                  <UFormField label="Date In Service">
                    <UInput v-model="form.date_in_service" type="date" class="w-full" />
                  </UFormField>
                  <UFormField label="Notes" class="col-span-2">
                    <UTextarea v-model="form.notes" :rows="3" class="w-full" />
                  </UFormField>
                </div>
                <UAlert v-if="editError" color="error" variant="soft" :description="editError" class="mt-4" />
              </div>

              <!-- Baler Info (read-only from model) -->
              <div v-else-if="activeTab === 'baler'" class="px-6 py-5">
                <div v-if="modelData" class="space-y-5">
                  <!-- Header banner -->
                  <div class="flex items-center gap-3 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 px-5 py-4 text-white shadow-sm">
                    <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white/15">
                      <UIcon name="i-heroicons-cube" class="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p class="text-sm font-semibold">{{ modelData.model_no }}</p>
                      <p class="text-xs text-blue-100 capitalize">{{ modelData.baler_type ?? "" }} · {{ modelData.baler_size ?? "—" }}</p>
                    </div>
                  </div>

                  <!-- Spec cards -->
                  <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
                    <div class="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3">
                      <p class="text-xs font-medium text-blue-400">Bale Weight</p>
                      <p class="mt-1 text-xl font-bold text-blue-700">{{ modelData.bale_weight ?? "—" }}<span v-if="modelData.bale_weight" class="ml-1 text-sm font-medium text-blue-400">kg</span></p>
                    </div>
                    <div class="rounded-xl border border-violet-100 bg-violet-50 px-4 py-3">
                      <p class="text-xs font-medium text-violet-400">Bale Time</p>
                      <p class="mt-1 text-xl font-bold text-violet-700">{{ modelData.bale_time ?? "—" }}<span v-if="modelData.bale_time" class="ml-1 text-sm font-medium text-violet-400">min</span></p>
                    </div>
                    <div class="rounded-xl border border-amber-100 bg-amber-50 px-4 py-3">
                      <p class="text-xs font-medium text-amber-400">Ram Force</p>
                      <p class="mt-1 text-xl font-bold text-amber-700">{{ modelData.ram_force ?? "—" }}<span v-if="modelData.ram_force" class="ml-1 text-sm font-medium text-amber-400">kN</span></p>
                    </div>
                    <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                      <p class="text-xs font-medium text-slate-400">Baler Type</p>
                      <p class="mt-1 text-base font-semibold capitalize text-slate-700">{{ modelData.baler_type ?? "—" }}</p>
                    </div>
                    <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                      <p class="text-xs font-medium text-slate-400">Baler Size</p>
                      <p class="mt-1 text-base font-semibold capitalize text-slate-700">{{ modelData.baler_size ?? "—" }}</p>
                    </div>
                    <div class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                      <p class="text-xs font-medium text-slate-400">Bale Size</p>
                      <p class="mt-1 text-base font-semibold text-slate-700">{{ modelData.bale_size ?? "—" }}</p>
                    </div>
                  </div>

                  <p class="text-xs text-slate-400">Edit specs via Settings → Asset Models.</p>
                </div>
                <div v-else class="flex h-48 items-center justify-center">
                  <p class="text-sm text-slate-400">No model assigned or baler specs not set. Edit specs in Settings → Asset Models.</p>
                </div>
              </div>

              <!-- Scores -->
              <div v-else-if="activeTab === 'scores'" class="px-6 py-5">

                <!-- View mode -->
                <template v-if="!editingScores">
                  <div class="mb-5 flex items-start justify-between gap-4">
                    <!-- Total + tier + risk flag -->
                    <div v-if="scoresData">
                      <div class="flex items-center gap-6">
                        <!-- Criticality score -->
                        <div>
                          <p class="text-xs text-slate-400 mb-0.5">Criticality Score</p>
                          <div class="flex items-baseline gap-2">
                            <span class="text-3xl font-bold text-slate-900">
                              {{ (scoresData.safety_score ?? 0) + (scoresData.operational_score ?? 0) + (scoresData.backup_score ?? 0) + (scoresData.repair_score ?? 0) + (scoresData.usage_score ?? 0) }}
                            </span>
                            <span class="text-sm text-slate-400">/ 12</span>
                            <span class="text-sm font-semibold" :class="getCriticalityTier((scoresData.safety_score ?? 0) + (scoresData.operational_score ?? 0) + (scoresData.backup_score ?? 0) + (scoresData.repair_score ?? 0) + (scoresData.usage_score ?? 0)).color">
                              {{ getCriticalityTier((scoresData.safety_score ?? 0) + (scoresData.operational_score ?? 0) + (scoresData.backup_score ?? 0) + (scoresData.repair_score ?? 0) + (scoresData.usage_score ?? 0)).label }}
                            </span>
                          </div>
                          <p class="mt-0.5 text-xs text-slate-400">10–12 Critical · 7–9 High · 4–6 Medium · 0–3 Low</p>
                        </div>
                        <!-- Risk flag -->
                        <div>
                          <p class="text-xs text-slate-400 mb-0.5">Risk Flag</p>
                          <span class="inline-flex items-center rounded-md border px-3 py-1 text-sm font-semibold"
                            :class="[getRiskFlag(scoresData).bg, getRiskFlag(scoresData).color]">
                            {{ getRiskFlag(scoresData).label }}
                          </span>
                          <p class="mt-0.5 text-xs text-slate-400">Based on usage &amp; operational impact</p>
                        </div>
                      </div>
                    </div>
                    <div v-else />
                    <UButton size="xs" variant="soft" icon="i-heroicons-pencil-square" @click="openScoresEdit">
                      {{ scoresData ? "Edit Scores" : "Add Scores" }}
                    </UButton>
                  </div>

                  <div v-if="scoresData" class="space-y-3">
                    <div v-for="f in scoreFields" :key="f.key"
                      class="flex items-center gap-4 rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
                      <!-- Score badge -->
                      <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white border border-slate-200">
                        <span class="text-lg font-bold text-slate-800">{{ scoresData[f.key] ?? "—" }}</span>
                      </div>
                      <!-- Label + description -->
                      <div class="min-w-0 flex-1">
                        <p class="text-sm font-medium text-slate-800">{{ f.label }} <span class="font-normal text-slate-400">(0–{{ f.max }})</span></p>
                        <p class="text-xs text-slate-500">{{ f.question }}</p>
                        <p v-if="scoresData[f.key] != null" class="mt-0.5 text-xs text-slate-400 italic">{{ f.levels[scoresData[f.key]!] }}</p>
                      </div>
                      <!-- Bar -->
                      <div class="hidden sm:block w-24 shrink-0">
                        <div class="h-2 w-full rounded-full bg-slate-200">
                          <div class="h-2 rounded-full bg-primary-500 transition-all"
                            :style="{ width: `${((scoresData[f.key] ?? 0) / f.max) * 100}%` }" />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-else class="flex h-32 items-center justify-center rounded-lg border border-dashed border-slate-200">
                    <p class="text-sm text-slate-400">No scores recorded yet. Click "Add Scores" to get started.</p>
                  </div>
                </template>

                <!-- Edit mode -->
                <template v-else>
                  <div class="mb-1 flex items-center justify-between">
                    <h4 class="text-sm font-semibold text-slate-700">Asset Criticality Scores</h4>
                    <p class="text-xs text-slate-400">Maximum total: 12</p>
                  </div>
                  <p class="mb-4 text-xs text-slate-500">Rate each criterion using the guide below. Higher scores indicate greater criticality.</p>

                  <div class="space-y-4">
                    <div v-for="f in scoreFields" :key="f.key" class="rounded-lg border border-slate-200 p-4">
                      <div class="flex items-start gap-4">
                        <div class="flex-1 min-w-0">
                          <p class="text-sm font-medium text-slate-800">{{ f.label }}</p>
                          <p class="text-xs text-slate-500 mt-0.5">{{ f.question }}</p>
                          <div class="mt-2 space-y-0.5">
                            <p v-for="(desc, i) in f.levels" :key="i" class="text-xs text-slate-400">
                              <span class="font-medium text-slate-500">{{ i }}</span> — {{ desc }}
                            </p>
                          </div>
                        </div>
                        <div class="shrink-0 w-24">
                          <UFormField :label="`Score (0–${f.max})`">
                            <UInput v-model.number="(scoresForm as any)[f.key]" type="number" min="0" :max="f.max" class="w-full" />
                          </UFormField>
                        </div>
                      </div>
                    </div>
                  </div>

                  <UAlert v-if="scoresError" color="error" variant="soft" :description="scoresError" class="mt-4" />
                  <div class="mt-5 flex justify-end gap-3">
                    <UButton variant="ghost" color="neutral" @click="editingScores = false">Cancel</UButton>
                    <UButton :loading="savingScores" @click="saveScores">Save Scores</UButton>
                  </div>
                </template>
              </div>

              <!-- Open Work Orders -->
              <div v-else-if="activeTab === 'open-wo'" class="divide-y divide-slate-50 px-6 py-2">
                <div v-for="wo in openWorkOrders" :key="wo.work_order_id" class="flex items-start gap-3 py-3">
                  <div class="min-w-0 flex-1">
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-medium text-slate-700">#{{ wo.work_order_id }}</span>
                      <UBadge :color="woStatusColors[wo.status] ?? 'neutral'" variant="soft" size="xs" class="capitalize">{{ wo.status.replace(/_/g, " ") }}</UBadge>
                      <UBadge color="neutral" variant="soft" size="xs" class="capitalize">{{ wo.priority }}</UBadge>
                    </div>
                    <p class="mt-0.5 truncate text-sm text-slate-600">{{ wo.description ?? "—" }}</p>
                    <p class="text-xs text-slate-400">Issued: {{ fmtDate(wo.issue_date) }}<span v-if="wo.expected_date"> · Due: {{ fmtDate(wo.expected_date) }}</span></p>
                  </div>
                </div>
              </div>

              <!-- Recent Work Orders -->
              <div v-else-if="activeTab === 'recent-wo'">
                <div v-if="recentWorkOrders.length" class="divide-y divide-slate-50 px-6 py-2">
                  <div v-for="wo in recentWorkOrders" :key="wo.work_order_id" class="flex items-start gap-3 py-3">
                    <div class="min-w-0 flex-1">
                      <div class="flex items-center gap-2">
                        <span class="text-xs font-medium text-slate-700">#{{ wo.work_order_id }}</span>
                        <UBadge :color="woStatusColors[wo.status] ?? 'neutral'" variant="soft" size="xs" class="capitalize">{{ wo.status.replace(/_/g, " ") }}</UBadge>
                      </div>
                      <p class="mt-0.5 truncate text-sm text-slate-600">{{ wo.description ?? "—" }}</p>
                      <p class="text-xs text-slate-400">Completed: {{ fmtDate(wo.date_completed) }}</p>
                    </div>
                  </div>
                </div>
                <div v-else class="flex h-48 items-center justify-center">
                  <p class="text-sm text-slate-400">No completed work orders for this asset.</p>
                </div>
              </div>

              <!-- Downtime -->
              <div v-else-if="activeTab === 'downtime'">
                <div v-if="downtimeData.length" class="divide-y divide-slate-100 px-6 py-1">
                  <div v-for="d in [...downtimeData].sort((a, b) => (b.start_date ?? '').localeCompare(a.start_date ?? '')).slice(0, 20)" :key="d.downtime_id" class="py-3">
                    <div class="flex items-center justify-between gap-4">
                      <div class="flex items-center gap-2">
                        <span class="text-sm font-medium text-slate-800">{{ fmtDateShort(d.start_date) }}</span>
                        <span v-if="d.end_date && d.end_date !== d.start_date" class="text-xs text-slate-400">→ {{ fmtDateShort(d.end_date) }}</span>
                      </div>
                      <div class="flex items-center gap-2 shrink-0">
                        <span class="text-sm font-semibold text-red-600">{{ d.downtime_hours?.toFixed(1) ?? "—" }}h</span>
                        <UBadge :color="d.planned ? 'info' : 'error'" variant="soft" size="xs">{{ d.planned ? "Planned" : "Unplanned" }}</UBadge>
                        <UBadge v-if="d.repeat_failure" color="warning" variant="soft" size="xs">Repeat</UBadge>
                      </div>
                    </div>
                    <p v-if="d.details" class="mt-1 truncate text-sm text-slate-600" :title="d.details">{{ d.details }}</p>
                    <div class="mt-1 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-slate-400">
                      <span v-if="d.component_affected"><span class="font-medium text-slate-500">Component:</span> {{ d.component_affected }}</span>
                      <span v-if="d.root_cause"><span class="font-medium text-slate-500">Cause:</span> {{ d.root_cause }}</span>
                      <span v-if="d.temporary_fix" class="text-amber-500">Temporary fix applied</span>
                    </div>
                  </div>
                </div>
                <div v-else class="flex h-48 items-center justify-center">
                  <p class="text-sm text-slate-400">No downtime records for this asset.</p>
                </div>
              </div>

              <!-- Inspections -->
              <div v-else-if="activeTab === 'inspections'">
                <div v-if="inspectionsData.length" class="divide-y divide-slate-50 px-6 py-2">
                  <div v-for="ins in inspectionsData.slice(0, 15)" :key="ins.id" class="flex items-center justify-between py-3 text-sm">
                    <div>
                      <p class="font-medium text-slate-700">{{ ins.inspection_no }}</p>
                      <p class="text-xs text-slate-400">{{ fmtDate(ins.inspection_date) }}</p>
                    </div>
                    <UBadge :color="ins.overall_result === 'pass' ? 'success' : ins.overall_result === 'fail' ? 'error' : 'warning'" variant="soft" size="xs" class="capitalize">
                      {{ ins.overall_result }}
                    </UBadge>
                  </div>
                </div>
                <div v-else class="flex h-48 items-center justify-center">
                  <p class="text-sm text-slate-400">No inspection records for this asset.</p>
                </div>
              </div>

              <!-- Issues -->
              <div v-else-if="activeTab === 'issues'">
                <div v-if="issuesData.length" class="divide-y divide-slate-50 px-6 py-2">
                  <div v-for="issue in issuesData" :key="issue.id" class="flex items-start justify-between gap-3 py-3 text-sm">
                    <div class="min-w-0 flex-1">
                      <p class="truncate text-slate-700">{{ issue.description }}</p>
                      <p class="text-xs text-slate-400">{{ fmtDate(issue.reported_at) }}</p>
                    </div>
                    <div class="flex shrink-0 gap-1">
                      <UBadge :color="severityColors[issue.severity]" variant="soft" size="xs" class="capitalize">{{ issue.severity }}</UBadge>
                      <UBadge color="neutral" variant="soft" size="xs" class="capitalize">{{ issue.status.replace(/_/g, " ") }}</UBadge>
                    </div>
                  </div>
                </div>
                <div v-else class="flex h-48 items-center justify-center">
                  <p class="text-sm text-slate-400">No issues reported for this asset.</p>
                </div>
              </div>

            </div>

            <!-- Footer — always pinned at bottom -->
            <div class="flex shrink-0 justify-end gap-3 border-t border-slate-100 px-6 py-4">
              <UButton variant="ghost" color="neutral" @click="showViewModal = false">Close</UButton>
              <UButton v-if="activeTab === 'details'" :loading="savingEdit" @click="saveEdit">Save Changes</UButton>
            </div>
          </template>

        </div>
      </template>
    </UModal>

    <!-- Delete Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Asset</h3></template>
          <p class="text-sm text-slate-500">Delete asset <strong>{{ deleteTarget?.asset_id }}</strong>? This cannot be undone.</p>
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
