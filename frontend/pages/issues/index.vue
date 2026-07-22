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
  (assets.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id }))
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
        <div class="flex items-center justify-between gap-3">
          <div class="flex flex-wrap items-center gap-3">
            <UInput v-model="search" placeholder="Search by asset or description..." leading-icon="i-heroicons-magnifying-glass" class="max-w-xs" />
            <USelect v-model="statusFilter" :items="filterStatusOptions" class="w-44" />
            <USelect v-model="severityFilter" :items="filterSeverityOptions" class="w-44" />
          </div>
          <UButton leading-icon="i-heroicons-plus" @click="openCreate" class="!bg-blue-700 hover:!bg-blue-800">Report Issue</UButton>
        </div>
      </template>

      <!-- Issue card list -->
      <div class="overflow-auto h-full p-4 space-y-2">
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
