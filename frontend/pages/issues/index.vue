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

const columns = [
  { accessorKey: "id", header: "ID" },
  { accessorKey: "asset_id", header: "Asset" },
  { accessorKey: "severity", header: "Severity" },
  { accessorKey: "status", header: "Status" },
  { accessorKey: "reported_by", header: "Reported By" },
  { accessorKey: "reported_at", header: "Reported" },
  { accessorKey: "description", header: "Description" },
  { id: "actions", header: "" },
]

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
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <UButton leading-icon="i-heroicons-plus" @click="openCreate">Report Issue</UButton>
    </div>

    <!-- Summary badges -->
    <div class="flex flex-wrap gap-3">
      <div v-for="sev in severityOptions" :key="sev"
        class="flex items-center gap-2 rounded-lg border border-gray-100 bg-white px-3 py-2 shadow-sm">
        <UBadge :color="severityColors[sev]" variant="soft" size="xs" class="capitalize">{{ sev }}</UBadge>
        <span class="text-sm font-semibold text-slate-700">
          {{ (issues ?? []).filter((i) => i.severity === sev && i.status !== 'dismissed').length }}
        </span>
      </div>
    </div>

    <UCard>
      <template #header>
        <div class="flex flex-wrap items-center gap-3">
          <UInput v-model="search" placeholder="Search by asset or description..." leading-icon="i-heroicons-magnifying-glass" class="max-w-xs" />
          <USelect v-model="statusFilter" :items="filterStatusOptions" class="w-44" />
          <USelect v-model="severityFilter" :items="filterSeverityOptions" class="w-44" />
        </div>
      </template>

      <UTable :data="filtered" :columns="columns">
        <template #severity-cell="{ row: { original: row } }">
          <UBadge :color="severityColors[row.severity]" variant="soft" class="capitalize">
            {{ row.severity }}
          </UBadge>
        </template>
        <template #status-cell="{ row: { original: row } }">
          <UBadge :color="statusColors[row.status]" variant="soft" class="capitalize">
            {{ row.status.replace(/_/g, " ") }}
          </UBadge>
        </template>
        <template #reported_by-cell="{ row: { original: row } }">
          {{ row.reported_by ? userMap[row.reported_by] ?? `User ${row.reported_by}` : "—" }}
        </template>
        <template #reported_at-cell="{ row: { original: row } }">
          {{ formatDate(row.reported_at) }}
        </template>
        <template #description-cell="{ row: { original: row } }">
          <span class="line-clamp-1 max-w-xs text-slate-600">{{ row.description }}</span>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton
              v-if="row.status === 'open' || row.status === 'in_review'"
              variant="ghost" size="xs" icon="i-heroicons-arrow-path"
              color="success" title="Convert to Work Order"
              @click="openConvert(row)"
            />
            <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEdit(row)" />
            <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Create / Edit Modal -->
    <UModal v-model:open="showFormModal">
      <template #content>
        <div class="flex max-h-[90vh] w-full flex-col rounded-xl bg-white shadow-xl">
          <div class="flex shrink-0 items-center justify-between border-b border-slate-100 px-6 py-5">
            <div>
              <h3 class="text-base font-semibold text-slate-900">{{ isEditing ? "Edit Issue" : "Report Issue" }}</h3>
              <p class="text-sm text-slate-500">{{ isEditing ? "Update issue details" : "Log a new issue for review" }}</p>
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
          <div class="flex shrink-0 justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showFormModal = false">Cancel</UButton>
            <UButton :loading="saving" @click="save">{{ isEditing ? "Save Changes" : "Report Issue" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Convert to Work Order Modal -->
    <UModal v-model:open="showConvertModal" :ui="{ content: 'max-w-2xl' }">
      <template #content>
        <div class="flex max-h-[90vh] w-full flex-col rounded-xl bg-white shadow-xl">
          <div class="flex shrink-0 items-start gap-4 border-b border-slate-100 px-6 py-5">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-green-50">
              <UIcon name="i-heroicons-arrow-path" class="h-5 w-5 text-green-600" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900">Convert to Work Order</h3>
              <p class="text-sm text-slate-500">Issue #{{ convertingIssue?.id }} — {{ convertingIssue?.asset_id }}</p>
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
          <div class="flex shrink-0 justify-end gap-3 border-t border-slate-100 px-6 py-4">
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
          <p class="text-sm text-slate-500">Delete issue <strong>#{{ deleteTarget?.id }}</strong>? This cannot be undone.</p>
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
