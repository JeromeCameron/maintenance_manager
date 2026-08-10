<script setup lang="ts">
import type { Issue, WorkOrder } from "~/types"

const { isAdmin } = useAuth()
const { getAll, create, update, remove } = useIssues()
const { getAll: getAssets } = useAssets()
const { getAll: getUsers } = useUsers()
const { create: createWorkOrder } = useWorkOrders()

const { data: issues, refresh } = await useAsyncData("issues", () => getAll())
const [{ data: assets }, { data: users }] = await Promise.all([
  useAsyncData("assets-select", () => getAssets()),
  useAsyncData("users-select", () => getUsers()),
])

// ── Options ───────────────────────────────────────────────────
const assetOptions = computed(() =>
  [...(assets.value ?? [])]
    .sort((a, b) => a.asset_id.localeCompare(b.asset_id))
    .map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id }))
)
const userOptions = computed(() =>
  [{ label: "Unknown", value: undefined }, ...(users.value ?? []).map((u) => ({ label: `${u.firstname} ${u.lastname}`, value: u.id }))]
)
const severityOptions = ["low", "medium", "high", "critical"]
const statusOptions = ["open", "in_review", "converted", "dismissed"]

const severityColors: Record<string, string> = {
  low: "success", medium: "warning", high: "error", critical: "error",
}
const statusColors: Record<string, string> = {
  open: "info", in_review: "warning", converted: "success", dismissed: "neutral",
}
const statusDotClass: Record<string, string> = {
  open: "bg-blue-500", in_review: "bg-amber-500", converted: "bg-green-500", dismissed: "bg-slate-400",
}
const statusLabels: Record<string, string> = {
  open: "Open", in_review: "In Review", converted: "Converted", dismissed: "Dismissed",
}

const userMap = computed(() => {
  const m: Record<number, string> = {}
  for (const u of users.value ?? []) { if (u.id != null) m[u.id] = `${u.firstname} ${u.lastname}` }
  return m
})

// ── Filters ───────────────────────────────────────────────────
const search = ref("")
const severityFilter = ref<string | null>(null)
const statusFilter = ref<string | null>(null)

const filterStatusOptions = [
  { label: "All statuses", value: null },
  ...statusOptions.map((s) => ({ label: s.replace(/_/g, " "), value: s })),
]
const filterSeverityOptions = [
  { label: "All severities", value: null },
  ...severityOptions.map((s) => ({ label: s, value: s })),
]

const filtered = computed(() =>
  (issues.value ?? []).filter((i) => {
    const q = search.value.toLowerCase()
    const matchSearch = !q || (i.asset_id ?? "").toLowerCase().includes(q) || i.description.toLowerCase().includes(q)
    const matchStatus = !statusFilter.value || i.status === statusFilter.value
    const matchSeverity = !severityFilter.value || i.severity === severityFilter.value
    return matchSearch && matchStatus && matchSeverity
  })
)

// ── View switcher (List / Kanban) ───────────────────────────────
const viewMode = ref<"list" | "kanban">("list")

const groups = computed(() =>
  statusOptions
    .filter((s) => !statusFilter.value || s === statusFilter.value)
    .map((s) => ({
      status: s,
      label: statusLabels[s],
      dot: statusDotClass[s],
      issues: filtered.value.filter((i) => i.status === s),
    }))
)

// ── Kanban drag-and-drop (native HTML5 DnD, no extra dependency) ──
const draggedIssue = ref<Issue | null>(null)
const dragOverStatus = ref<string | null>(null)

function onDragStart(issue: Issue) {
  draggedIssue.value = issue
}
async function onDrop(status: string) {
  dragOverStatus.value = null
  const issue = draggedIssue.value
  draggedIssue.value = null
  if (!issue || issue.status === status) return
  // "Converted" requires an actual linked work order, so route through the
  // existing convert flow rather than silently flipping the status.
  if (status === "converted") {
    openConvert(issue)
    return
  }
  await update(issue.id!, { ...issue, status: status as Issue["status"] })
  await refresh()
}

// ── Create / Edit modal ───────────────────────────────────────
const showFormModal = ref(false)
const isEditing = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)

const defaultForm = (): Partial<Issue> => ({
  severity: "medium",
  status: "open",
  reported_at: new Date().toISOString(),
})
const form = ref<Partial<Issue>>(defaultForm())

function openCreate() {
  form.value = defaultForm()
  isEditing.value = false
  editId.value = null
  formError.value = null
  showFormModal.value = true
}

function openEdit(row: Issue) {
  form.value = { ...row }
  isEditing.value = true
  editId.value = row.id!
  formError.value = null
  showFormModal.value = true
}

async function save() {
  saving.value = true
  formError.value = null
  try {
    if (isEditing.value && editId.value) {
      await update(editId.value, form.value as Issue)
    } else {
      await create(form.value as Issue)
    }
    await refresh()
    showFormModal.value = false
  } catch (e: unknown) {
    formError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    saving.value = false
  }
}

// ── Convert to Work Order modal ───────────────────────────────
const showConvertModal = ref(false)
const convertingIssue = ref<Issue | null>(null)
const convertForm = ref<Partial<WorkOrder>>({})
const converting = ref(false)
const convertError = ref<string | null>(null)

const woTypeOptions = ["corrective", "predictive", "preventative", "inspection", "project"]
const woPriorityOptions = ["Low", "Medium", "High"]

function openConvert(issue: Issue) {
  convertingIssue.value = issue
  convertForm.value = {
    asset_id: issue.asset_id,
    description: issue.description,
    priority: issue.severity === "critical" || issue.severity === "high" ? "High" : issue.severity === "medium" ? "Medium" : "Low",
    typ: "corrective",
    status: "requested",
    issue_date: new Date().toISOString().slice(0, 10),
  }
  convertError.value = null
  showConvertModal.value = true
}

async function submitConvert() {
  if (!convertingIssue.value) return
  converting.value = true
  convertError.value = null
  try {
    const wo = await createWorkOrder(convertForm.value as WorkOrder)
    await update(convertingIssue.value.id!, { status: "converted", work_order_id: wo.work_order_id })
    await refresh()
    showConvertModal.value = false
  } catch (e: unknown) {
    convertError.value = (e as { message?: string }).message ?? "Conversion failed"
  } finally {
    converting.value = false
  }
}

// ── Delete modal ──────────────────────────────────────────────
const deleteTarget = ref<Issue | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value?.id) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.id)
    await refresh()
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}

function formatDate(val: string | undefined) {
  if (!val) return "—"
  return new Date(val).toLocaleDateString()
}
</script>

<template>
  <div class="flex min-h-full flex-col gap-4">
    <!-- Summary badges -->
    <div class="flex flex-wrap gap-3">
      <div v-for="sev in severityOptions" :key="sev"
        class="flex items-center gap-2 rounded-lg border border-gray-100 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 py-2 shadow-sm">
        <UBadge :color="severityColors[sev]" variant="soft" size="xs" class="capitalize">{{ sev }}</UBadge>
        <span class="text-sm font-semibold text-slate-700 dark:text-slate-300">
          {{ (issues ?? []).filter((i) => i.severity === sev && i.status !== 'dismissed').length }}
        </span>
      </div>
    </div>

    <UCard :ui="{ root: 'flex flex-col flex-1 min-h-0', body: 'flex flex-col flex-1 min-h-0 p-0' }">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="flex flex-wrap items-center gap-3">
            <div class="flex items-center gap-0.5 rounded-lg bg-slate-100 p-0.5 dark:bg-slate-800">
              <button
                type="button"
                class="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors"
                :class="viewMode === 'list' ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-slate-100' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'"
                @click="viewMode = 'list'"
              >
                <UIcon name="i-heroicons-bars-3-bottom-left" class="h-3.5 w-3.5" />
                List
              </button>
              <button
                type="button"
                class="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-colors"
                :class="viewMode === 'kanban' ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-700 dark:text-slate-100' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'"
                @click="viewMode = 'kanban'"
              >
                <UIcon name="i-heroicons-view-columns" class="h-3.5 w-3.5" />
                Kanban
              </button>
            </div>
            <UInput v-model="search" placeholder="Search by asset or description..." leading-icon="i-heroicons-magnifying-glass" class="max-w-xs" />
            <USelect v-model="statusFilter" :items="filterStatusOptions" class="w-44" />
            <USelect v-model="severityFilter" :items="filterSeverityOptions" class="w-44" />
          </div>
          <UButton leading-icon="i-heroicons-plus" @click="openCreate" class="!bg-blue-700 hover:!bg-blue-800">Report Issue</UButton>
        </div>
      </template>

      <!-- Issue card list -->
      <div v-if="viewMode === 'list'" class="overflow-auto h-full p-4 space-y-2">
        <div v-if="filtered.length === 0" class="py-12 text-center text-sm text-gray-400 dark:text-slate-500">
          No issues found.
        </div>
        <div
          v-for="issue in filtered"
          :key="issue.id"
          class="flex cursor-pointer items-start gap-4 rounded-lg px-5 py-4 ring-1 ring-gray-200 dark:ring-slate-700 hover:bg-blue-50/40 dark:hover:bg-blue-500/10 transition-colors border-l-4"
          :class="issue.severity === 'critical' || issue.severity === 'high' ? 'border-l-red-400' : issue.severity === 'medium' ? 'border-l-yellow-400' : 'border-l-transparent'"
          @click="openEdit(issue)"
        >
          <!-- Left icon -->
          <div class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gray-100 dark:bg-slate-800">
            <UIcon name="i-heroicons-exclamation-triangle" class="h-4 w-4 text-gray-400 dark:text-slate-500" />
          </div>

          <!-- Main content -->
          <div class="min-w-0 flex-1">
            <!-- Title -->
            <div class="flex items-center gap-2">
              <span class="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate">{{ issue.description }}</span>
            </div>
            <!-- Asset -->
            <p class="mt-0.5 text-xs text-gray-500 dark:text-slate-400">Asset: {{ issue.asset_id ?? "—" }}</p>
            <!-- Meta row -->
            <div class="mt-1.5 flex flex-wrap items-center gap-2">
              <UBadge :color="severityColors[issue.severity]" variant="soft" size="xs" class="capitalize">{{ issue.severity }}</UBadge>
              <span class="flex items-center gap-1 text-[11px] text-gray-500 dark:text-slate-400">
                <UIcon name="i-heroicons-user" class="h-3 w-3" />
                {{ issue.reported_by ? (userMap[issue.reported_by] ?? `User ${issue.reported_by}`) : "Unknown" }}
              </span>
              <span class="flex items-center gap-1 text-[11px] text-gray-400 dark:text-slate-500">
                <UIcon name="i-heroicons-calendar" class="h-3 w-3" />
                {{ formatDate(issue.reported_at) }}
              </span>
            </div>
          </div>

          <!-- Right side -->
          <div class="shrink-0 flex flex-col items-end gap-2">
            <UBadge :color="statusColors[issue.status]" variant="soft" size="xs" class="capitalize">{{ issue.status.replace(/_/g, " ") }}</UBadge>
            <div class="flex items-center gap-1">
              <UButton
                v-if="issue.status === 'open' || issue.status === 'in_review'"
                variant="ghost" size="xs" icon="i-heroicons-arrow-path"
                color="success" title="Convert to Work Order"
                @click.stop="openConvert(issue)"
              />
              <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click.stop="deleteTarget = issue" />
            </div>
          </div>
        </div>
      </div>

      <!-- Kanban view -->
      <div v-else class="flex h-full gap-3 overflow-x-auto p-3">
        <div
          v-for="group in groups"
          :key="group.status"
          class="flex w-72 shrink-0 flex-col rounded-lg bg-slate-50 transition-colors dark:bg-slate-800/60"
          :class="dragOverStatus === group.status ? 'ring-2 ring-blue-400' : ''"
          @dragover.prevent="dragOverStatus = group.status"
          @dragleave="dragOverStatus = null"
          @drop="onDrop(group.status)"
        >
          <div class="flex shrink-0 items-center gap-2 border-b border-gray-200 px-3 py-2.5 dark:border-slate-700">
            <span class="h-2.5 w-2.5 rounded-full" :class="group.dot" />
            <span class="text-xs font-semibold text-slate-700 dark:text-slate-200">{{ group.label }}</span>
            <span class="ml-auto rounded-full bg-white px-1.5 py-0.5 text-[10px] font-medium text-slate-400 ring-1 ring-gray-200 dark:bg-slate-900 dark:text-slate-500 dark:ring-slate-700">
              {{ group.issues.length }}
            </span>
          </div>

          <div class="flex-1 space-y-2 overflow-y-auto p-2">
            <div v-if="group.issues.length === 0" class="py-6 text-center text-xs text-gray-400 dark:text-slate-500">
              No issues
            </div>

            <div
              v-for="issue in group.issues"
              :key="issue.id"
              draggable="true"
              class="cursor-pointer rounded-lg border-l-4 bg-white p-3 shadow-sm ring-1 ring-gray-200 transition-shadow hover:ring-blue-300 dark:bg-slate-900 dark:ring-slate-700"
              :class="issue.severity === 'critical' || issue.severity === 'high' ? 'border-l-red-400' : issue.severity === 'medium' ? 'border-l-yellow-400' : 'border-l-transparent'"
              @dragstart="onDragStart(issue)"
              @dragend="dragOverStatus = null"
              @click="openEdit(issue)"
            >
              <div class="flex items-start justify-between gap-2">
                <span class="line-clamp-2 text-sm font-semibold text-slate-800 dark:text-slate-100">{{ issue.description }}</span>
                <UButton
                  v-if="issue.status === 'open' || issue.status === 'in_review'"
                  variant="ghost" size="xs" icon="i-heroicons-arrow-path"
                  color="success" title="Convert to Work Order"
                  @click.stop="openConvert(issue)"
                />
              </div>

              <p class="mt-1 text-xs text-gray-500 dark:text-slate-400">Asset: {{ issue.asset_id ?? "—" }}</p>

              <div class="mt-2 flex items-center justify-between gap-2">
                <UBadge :color="severityColors[issue.severity]" variant="soft" size="xs" class="capitalize">{{ issue.severity }}</UBadge>
                <span class="flex items-center gap-1 text-[10px] text-gray-400 dark:text-slate-500">
                  <UIcon name="i-heroicons-calendar" class="h-3 w-3" />
                  {{ formatDate(issue.reported_at) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </UCard>

    <!-- Create / Edit Modal -->
    <UModal v-model:open="showFormModal">
      <template #content>
        <div class="flex max-h-[90vh] w-full flex-col rounded-xl bg-white shadow-xl dark:bg-slate-900">
          <div class="flex shrink-0 items-center justify-between border-b border-slate-100 dark:border-slate-800 px-6 py-5">
            <div>
              <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">{{ isEditing ? "Edit Issue" : "Report Issue" }}</h3>
              <p class="text-sm text-slate-500 dark:text-slate-400">{{ isEditing ? "Update issue details" : "Log a new issue for review" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showFormModal = false" />
          </div>
          <div class="flex-1 overflow-y-auto px-6 py-5">
            <div class="grid grid-cols-2 gap-x-5 gap-y-4">
              <UFormField label="Asset" class="col-span-2">
                <USelect v-model="form.asset_id" :items="assetOptions" placeholder="Select asset" class="w-full" />
              </UFormField>
              <UFormField label="Severity">
                <USelect v-model="form.severity" :items="severityOptions" class="w-full" />
              </UFormField>
              <UFormField label="Status">
                <USelect v-model="form.status" :items="statusOptions" class="w-full" />
              </UFormField>
              <UFormField label="Reported By">
                <USelect v-model="form.reported_by" :items="userOptions" placeholder="Select user" class="w-full" />
              </UFormField>
              <UFormField label="Reported At">
                <UInput v-model="form.reported_at" type="datetime-local" class="w-full" />
              </UFormField>
              <UFormField label="Description" class="col-span-2">
                <UTextarea v-model="form.description" :rows="4" placeholder="Describe the issue in detail…" class="w-full" />
              </UFormField>
            </div>
            <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="mt-4" />
          </div>
          <div class="flex shrink-0 justify-end gap-3 border-t border-slate-100 dark:border-slate-800 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showFormModal = false">Cancel</UButton>
            <UButton :loading="saving" @click="save">{{ isEditing ? "Save Changes" : "Report Issue" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Convert to Work Order Modal -->
    <UModal v-model:open="showConvertModal" :ui="{ content: 'max-w-2xl' }">
      <template #content>
        <div class="flex max-h-[90vh] w-full flex-col rounded-xl bg-white shadow-xl dark:bg-slate-900">
          <div class="flex shrink-0 items-start gap-4 border-b border-slate-100 dark:border-slate-800 px-6 py-5">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-green-50 dark:bg-green-500/10">
              <UIcon name="i-heroicons-arrow-path" class="h-5 w-5 text-green-600 dark:text-green-400" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">Convert to Work Order</h3>
              <p class="text-sm text-slate-500 dark:text-slate-400">Issue #{{ convertingIssue?.id }} — {{ convertingIssue?.asset_id }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showConvertModal = false" />
          </div>
          <div class="flex-1 overflow-y-auto px-6 py-5">
            <div class="grid grid-cols-2 gap-x-5 gap-y-4">
              <UFormField label="Asset">
                <USelect v-model="convertForm.asset_id" :items="assetOptions" class="w-full" />
              </UFormField>
              <UFormField label="Priority">
                <USelect v-model="convertForm.priority" :items="woPriorityOptions" class="w-full" />
              </UFormField>
              <UFormField label="Type">
                <USelect v-model="convertForm.typ" :items="woTypeOptions" class="w-full" />
              </UFormField>
              <UFormField label="Issue Date">
                <UInput v-model="convertForm.issue_date" type="date" class="w-full" />
              </UFormField>
              <UFormField label="Expected Date">
                <UInput v-model="convertForm.expected_date" type="date" class="w-full" />
              </UFormField>
              <UFormField label="Estimated Hours">
                <UInput v-model.number="convertForm.estimated_hours" type="number" step="0.5" class="w-full" />
              </UFormField>
              <UFormField label="Description" class="col-span-2">
                <UTextarea v-model="convertForm.description" :rows="3" class="w-full" />
              </UFormField>
              <UFormField label="Notes" class="col-span-2">
                <UTextarea v-model="convertForm.notes" :rows="2" class="w-full" />
              </UFormField>
            </div>
            <UAlert v-if="convertError" color="error" variant="soft" :description="convertError" class="mt-4" />
          </div>
          <div class="flex shrink-0 justify-end gap-3 border-t border-slate-100 dark:border-slate-800 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showConvertModal = false">Cancel</UButton>
            <UButton color="success" :loading="converting" leading-icon="i-heroicons-check" @click="submitConvert">
              Create Work Order
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Issue</h3></template>
          <p class="text-sm text-slate-500 dark:text-slate-400">Delete issue <strong>#{{ deleteTarget?.id }}</strong>? This cannot be undone.</p>
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
