<script setup lang="ts">
import type { Asset, AssetModel, AssetScores, WorkOrder, Downtime, Inspection, Issue } from "~/types"

const { isAdmin } = useAuth()
const { getAll, getOne, create, update, remove, getScoreByAsset, getWorkOrders, getDowntimes, getInspections } = useAssets()
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
const workOrdersData = ref<WorkOrder[]>([])
const downtimeData = ref<Downtime[]>([])
const inspectionsData = ref<Inspection[]>([])
const issuesData = ref<Issue[]>([])

const isBaler = computed(() => form.value.category === "baler")

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
  showViewModal.value = true

  const asset = await getOne(id)
  form.value = { ...asset }

  const [scores, wos, downtimes, inspections, issues, model] = await Promise.all([
    getScoreByAsset(id).catch(() => null),
    getWorkOrders(id).catch(() => []),
    getDowntimes(id).catch(() => []),
    getInspections(id).catch(() => []),
    getIssuesByAsset(id).catch(() => []),
    (asset.category === "baler" && asset.model_no) ? getModelOne(asset.model_no).catch(() => null) : Promise.resolve(null),
  ])

  modelData.value = model
  scoresData.value = scores
  workOrdersData.value = wos ?? []
  downtimeData.value = downtimes ?? []
  inspectionsData.value = inspections ?? []
  issuesData.value = issues ?? []
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

function fmtDate(v?: string | null) { return v ? new Date(v).toLocaleDateString() : "—" }
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <UButton leading-icon="i-heroicons-plus" @click="openCreate">New Asset</UButton>
    </div>

    <UCard>
      <template #header>
        <UInput v-model="search" placeholder="Search by ID or manufacturer..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
      </template>
      <UTable :data="filtered" :columns="columns">
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
                <div v-if="modelData" class="space-y-4">
                  <p class="text-xs text-slate-400">Specs for model <strong>{{ modelData.model_no }}</strong>. Edit via Settings → Asset Models.</p>
                  <div class="grid grid-cols-2 gap-4 sm:grid-cols-3">
                    <div v-for="(label, key) in { baler_type: 'Baler Type', baler_size: 'Baler Size', bale_weight: 'Bale Weight (kg)', bale_time: 'Bale Time (min)', ram_force: 'Ram Force (kN)', bale_size: 'Bale Size' }"
                      :key="key"
                      class="rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
                      <p class="text-xs text-slate-400">{{ label }}</p>
                      <p class="mt-0.5 font-medium text-slate-800 capitalize">{{ (modelData as any)[key] ?? "—" }}</p>
                    </div>
                  </div>
                </div>
                <div v-else class="flex h-48 items-center justify-center">
                  <p class="text-sm text-slate-400">No model assigned or baler specs not set. Edit specs in Settings → Asset Models.</p>
                </div>
              </div>

              <!-- Scores -->
              <div v-else-if="activeTab === 'scores'" class="px-6 py-5">
                <div v-if="scoresData" class="grid grid-cols-3 gap-4 sm:grid-cols-5">
                  <div v-for="(label, key) in { operational_score: 'Operational', safety_score: 'Safety', backup_score: 'Backup', repair_score: 'Repair', usage_score: 'Usage' }" :key="key"
                    class="flex flex-col items-center rounded-lg border border-slate-100 bg-slate-50 p-4">
                    <span class="text-2xl font-bold" :class="(scoresData as any)[key] >= 7 ? 'text-green-600' : (scoresData as any)[key] >= 4 ? 'text-amber-500' : 'text-red-500'">
                      {{ (scoresData as any)[key] ?? "—" }}
                    </span>
                    <span class="mt-1 text-xs text-slate-500">{{ label }}</span>
                  </div>
                </div>
                <div v-else class="flex h-48 items-center justify-center">
                  <p class="text-sm text-slate-400">No scores recorded for this asset.</p>
                </div>
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
                <div v-if="downtimeData.length" class="divide-y divide-slate-50 px-6 py-2">
                  <div v-for="d in downtimeData.slice(0, 15)" :key="d.downtime_id" class="flex items-center justify-between py-3 text-sm">
                    <div>
                      <p class="font-medium text-slate-700">{{ fmtDate(d.start_date) }}</p>
                      <p class="text-xs text-slate-400">{{ d.component_affected ?? "—" }}</p>
                    </div>
                    <div class="text-right">
                      <p class="font-semibold text-red-600">{{ d.downtime_hours?.toFixed(1) ?? "—" }}h</p>
                      <UBadge :color="d.planned ? 'info' : 'error'" variant="soft" size="xs">{{ d.planned ? "Planned" : "Unplanned" }}</UBadge>
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
