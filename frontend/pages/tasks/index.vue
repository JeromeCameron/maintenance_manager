<script setup lang="ts">
import type { Task, TaskStatus, TaskPriority } from "~/types"

const { user, isAdmin, isModerator } = useAuth()
const { getAll, create, update, remove } = useTasks()
const { refresh: refreshReminders } = useTaskReminders()
const { getAll: getUsers } = useUsers()
const { getAll: getAssets } = useAssets()
const { getAll: getWorkOrders } = useWorkOrders()
const { getAll: getInspections } = useInspections()
const { getAll: getDowntimes } = useDowntime()
const { getAll: getIssues } = useIssues()
const { getPOs, getInvoices } = useFinance()

const { data: tasksData, refresh } = await useAsyncData("tasks", () => getAll())
const [
  { data: users },
  { data: assets },
  { data: workOrders },
  { data: inspections },
  { data: downtimes },
  { data: issues },
  { data: pos },
  { data: invoices },
] = await Promise.all([
  useAsyncData("users-select", () => getUsers()),
  useAsyncData("assets-select", () => getAssets()),
  useAsyncData("work-orders-select", () => getWorkOrders()),
  useAsyncData("inspections-select", () => getInspections()),
  useAsyncData("downtimes-select", () => getDowntimes()),
  useAsyncData("issues-select", () => getIssues()),
  useAsyncData("pos-select", () => getPOs()),
  useAsyncData("invoices-select", () => getInvoices()),
])

// ── Lookups ───────────────────────────────────────────────────
const userMap = computed(() =>
  Object.fromEntries((users.value ?? []).map((u) => [u.id, `${u.firstname} ${u.lastname}`]))
)
const assetMap = computed(() => Object.fromEntries((assets.value ?? []).map((a) => [a.asset_id, a.alias || a.asset_id])))
const workOrderMap = computed(() => Object.fromEntries((workOrders.value ?? []).map((w) => [w.work_order_id, `WO #${w.work_order_id}`])))
const inspectionMap = computed(() => Object.fromEntries((inspections.value ?? []).map((i) => [i.id, i.inspection_no])))
const downtimeMap = computed(() => Object.fromEntries((downtimes.value ?? []).map((d) => [d.downtime_id, `DT #${d.downtime_id}`])))
const issueMap = computed(() => Object.fromEntries((issues.value ?? []).map((i) => [i.id, `Issue #${i.id}`])))
const poMap = computed(() => Object.fromEntries((pos.value ?? []).map((p) => [p.po_no, p.po_no])))
const invoiceMap = computed(() => Object.fromEntries((invoices.value ?? []).map((inv) => [inv.id, inv.invoice_no])))

function initials(userId?: number): string {
  const u = (users.value ?? []).find((u) => u.id === userId)
  if (!u) return "?"
  return `${u.firstname[0] ?? ""}${u.lastname[0] ?? ""}`.toUpperCase()
}

interface RefChip { icon: string; label: string }
function referenceChips(task: Task): RefChip[] {
  const chips: RefChip[] = []
  if (task.asset_id) chips.push({ icon: "i-heroicons-cube", label: assetMap.value[task.asset_id] ?? task.asset_id })
  if (task.work_order_id) chips.push({ icon: "i-heroicons-clipboard-document-list", label: workOrderMap.value[task.work_order_id] ?? `WO #${task.work_order_id}` })
  if (task.inspection_id) chips.push({ icon: "i-heroicons-magnifying-glass", label: inspectionMap.value[task.inspection_id] ?? `Inspection #${task.inspection_id}` })
  if (task.downtime_id) chips.push({ icon: "i-heroicons-exclamation-triangle", label: downtimeMap.value[task.downtime_id] ?? `DT #${task.downtime_id}` })
  if (task.issue_id) chips.push({ icon: "i-heroicons-flag", label: issueMap.value[task.issue_id] ?? `Issue #${task.issue_id}` })
  if (task.po_no) chips.push({ icon: "i-heroicons-document-text", label: poMap.value[task.po_no] ?? task.po_no })
  if (task.invoice_id) chips.push({ icon: "i-heroicons-banknotes", label: invoiceMap.value[task.invoice_id] ?? `Invoice #${task.invoice_id}` })
  return chips
}

// ── Status / priority config ────────────────────────────────────
const STATUS_ORDER: TaskStatus[] = ["not_started", "in_progress", "on_hold", "completed", "archived"]
const statusLabels: Record<TaskStatus, string> = {
  not_started: "Not Started",
  in_progress: "In Progress",
  on_hold: "On Hold",
  completed: "Completed",
  archived: "Archived",
}
const statusDotClass: Record<TaskStatus, string> = {
  not_started: "bg-slate-400",
  in_progress: "bg-amber-500",
  on_hold: "bg-purple-500",
  completed: "bg-green-500",
  archived: "bg-slate-300",
}
const statusBadgeClass: Record<TaskStatus, string> = {
  not_started: "bg-slate-100 text-slate-500 ring-1 ring-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:ring-slate-700",
  in_progress: "bg-amber-50 text-amber-700 ring-1 ring-amber-200 dark:bg-amber-500/10 dark:text-amber-400 dark:ring-amber-500/30",
  on_hold: "bg-purple-50 text-purple-600 ring-1 ring-purple-200 dark:bg-purple-500/10 dark:text-purple-400 dark:ring-purple-500/30",
  completed: "bg-green-50 text-green-600 ring-1 ring-green-200 dark:bg-green-500/10 dark:text-green-400 dark:ring-green-500/30",
  archived: "bg-slate-100 text-slate-400 ring-1 ring-slate-200 dark:bg-slate-800 dark:text-slate-500 dark:ring-slate-700",
}
const priorityDotClass: Record<TaskPriority, string> = { low: "bg-slate-300", medium: "bg-blue-400", high: "bg-orange-500", urgent: "bg-red-500" }
const priorityBadgeClass: Record<TaskPriority, string> = {
  low: "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400",
  medium: "bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400",
  high: "bg-orange-50 text-orange-600 dark:bg-orange-500/10 dark:text-orange-400",
  urgent: "bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400",
}

const taskStatusOptions = STATUS_ORDER.map((s) => ({ label: statusLabels[s], value: s }))
const taskPriorityOptions: { label: string; value: TaskPriority }[] = (["low", "medium", "high", "urgent"] as TaskPriority[])
  .map((p) => ({ label: p.charAt(0).toUpperCase() + p.slice(1), value: p }))

// ── Filters ───────────────────────────────────────────────────
const search = ref("")
const statusFilter = ref<TaskStatus | null>(null)
const priorityFilter = ref<TaskPriority | null>(null)
const assignedToMeOnly = ref(false)

const statusFilterOptions = [{ label: "All statuses", value: null }, ...taskStatusOptions]
const priorityFilterOptions = [{ label: "All priorities", value: null }, ...taskPriorityOptions]

const filtered = computed(() =>
  (tasksData.value ?? []).filter((t) => {
    const q = search.value.toLowerCase()
    const matchSearch = !q || t.title.toLowerCase().includes(q) || (t.description ?? "").toLowerCase().includes(q)
    const matchStatus = !statusFilter.value || t.status === statusFilter.value
    const matchPriority = !priorityFilter.value || t.priority === priorityFilter.value
    const matchMine = !assignedToMeOnly.value || t.assigned_to === user.value?.user_id || t.user_id === user.value?.user_id
    return matchSearch && matchStatus && matchPriority && matchMine
  })
)

// Backend already sorts by due_date ascending (nulls last); filtering here preserves that order.
const groups = computed(() =>
  STATUS_ORDER
    .filter((s) => !statusFilter.value || s === statusFilter.value)
    .map((s) => ({
      status: s,
      label: statusLabels[s],
      dot: statusDotClass[s],
      tasks: filtered.value.filter((t) => t.status === s),
    }))
)

// ── Helpers ───────────────────────────────────────────────────
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
function formatDate(value: string | null | undefined): string {
  if (!value) return "—"
  const [year, month, day] = value.slice(0, 10).split("-").map(Number)
  if (!year || !month || !day) return "—"
  return `${String(day).padStart(2, "0")}-${MONTHS[month - 1]}-${String(year).slice(-2)}`
}

const DONE_STATUSES: TaskStatus[] = ["completed", "archived"]
function isOverdue(task: Task): boolean {
  if (!task.due_date || DONE_STATUSES.includes(task.status)) return false
  return task.due_date < new Date().toISOString().slice(0, 10)
}
function isDueSoon(task: Task): boolean {
  if (!task.due_date || DONE_STATUSES.includes(task.status) || isOverdue(task)) return false
  const threshold = new Date()
  threshold.setDate(threshold.getDate() + 3)
  return task.due_date <= threshold.toISOString().slice(0, 10)
}

async function quickStatusChange(task: Task, newStatus: TaskStatus) {
  await update(task.id!, { ...task, status: newStatus })
  await refresh()
  await refreshReminders()
}

// ── View switcher (List / Kanban) ────────────────────────────────
const viewMode = ref<"list" | "kanban">("list")

// ── Kanban drag-and-drop (native HTML5 DnD, no extra dependency) ──
const draggedTask = ref<Task | null>(null)
const dragOverStatus = ref<TaskStatus | null>(null)

function onDragStart(task: Task) {
  draggedTask.value = task
}
function onDrop(status: TaskStatus) {
  dragOverStatus.value = null
  const task = draggedTask.value
  draggedTask.value = null
  if (task && task.status !== status) quickStatusChange(task, status)
}

// ── Form options ──────────────────────────────────────────────
const userOptions = computed(() => (users.value ?? []).map((u) => ({ label: `${u.firstname} ${u.lastname}`, value: u.id })))
const assetOptions = computed(() => [{ label: "None", value: undefined }, ...(assets.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id }))])
const workOrderOptions = computed(() => [{ label: "None", value: undefined }, ...(workOrders.value ?? []).map((w) => ({ label: `#${w.work_order_id} — ${(w.description ?? "").slice(0, 40)}`, value: w.work_order_id }))])
const inspectionOptions = computed(() => [{ label: "None", value: undefined }, ...(inspections.value ?? []).map((i) => ({ label: i.inspection_no, value: i.id }))])
const downtimeOptions = computed(() => [{ label: "None", value: undefined }, ...(downtimes.value ?? []).map((d) => ({ label: `#${d.downtime_id} — ${(d.details ?? d.asset_id ?? "").toString().slice(0, 30)}`, value: d.downtime_id }))])
const issueOptions = computed(() => [{ label: "None", value: undefined }, ...(issues.value ?? []).map((i) => ({ label: `#${i.id} — ${i.description.slice(0, 40)}`, value: i.id }))])
const poOptions = computed(() => [{ label: "None", value: undefined }, ...(pos.value ?? []).map((p) => ({ label: p.po_no, value: p.po_no }))])
const invoiceOptions = computed(() => [{ label: "None", value: undefined }, ...(invoices.value ?? []).map((inv) => ({ label: inv.invoice_no, value: inv.id }))])

// ── Create / Edit modal ─────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)

const defaultForm = (): Partial<Task> => ({ status: "not_started", priority: "medium" })
const form = ref<Partial<Task>>(defaultForm())

function openCreate() {
  form.value = defaultForm()
  isEditing.value = false
  editId.value = null
  formError.value = null
  showModal.value = true
}

function openEdit(task: Task) {
  form.value = { ...task }
  isEditing.value = true
  editId.value = task.id!
  formError.value = null
  showModal.value = true
}

async function save() {
  saving.value = true
  formError.value = null
  try {
    if (isEditing.value && editId.value) {
      await update(editId.value, form.value as Task)
    } else {
      await create(form.value as Task)
    }
    await refresh()
    await refreshReminders()
    showModal.value = false
  } catch (e: unknown) {
    formError.value = (e as { data?: { detail?: string }; message?: string }).data?.detail ?? (e as { message?: string }).message ?? "Save failed"
  } finally {
    saving.value = false
  }
}

// ── Delete modal ──────────────────────────────────────────────
const deleteTarget = ref<Task | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value?.id) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.id)
    await refresh()
    await refreshReminders()
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="flex min-h-full flex-col gap-4">
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
            <UInput v-model="search" placeholder="Search tasks…" leading-icon="i-heroicons-magnifying-glass" class="max-w-xs" />
            <USelect v-model="statusFilter" :items="statusFilterOptions" class="w-44" />
            <USelect v-model="priorityFilter" :items="priorityFilterOptions" class="w-40" />
            <UButton
              v-if="isAdmin || isModerator"
              :variant="assignedToMeOnly ? 'solid' : 'outline'"
              size="sm"
              color="neutral"
              @click="assignedToMeOnly = !assignedToMeOnly"
            >
              Assigned to me
            </UButton>
          </div>
          <UButton leading-icon="i-heroicons-plus" @click="openCreate" class="!bg-blue-700 hover:!bg-blue-800">New Task</UButton>
        </div>
      </template>

      <!-- List view -->
      <div v-if="viewMode === 'list'" class="overflow-auto h-full">
        <template v-for="group in groups" :key="group.status">
          <div class="sticky top-0 z-10 flex items-center gap-2 border-b border-t border-gray-100 bg-slate-50/90 px-5 py-2 backdrop-blur dark:border-slate-800 dark:bg-slate-800/80">
            <span class="h-2.5 w-2.5 rounded-full" :class="group.dot" />
            <span class="text-xs font-semibold text-slate-700 dark:text-slate-200">{{ group.label }}</span>
            <span class="rounded-full bg-white px-1.5 py-0.5 text-[10px] font-medium text-slate-400 ring-1 ring-gray-200 dark:bg-slate-900 dark:text-slate-500 dark:ring-slate-700">
              {{ group.tasks.length }}
            </span>
          </div>

          <div v-if="group.tasks.length === 0" class="px-5 py-6 text-center text-xs text-gray-400 dark:text-slate-500">
            No tasks
          </div>

          <div
            v-for="task in group.tasks"
            :key="task.id"
            class="flex cursor-pointer items-start gap-4 border-b border-gray-50 px-5 py-3 transition-colors hover:bg-blue-50/40 border-l-4 dark:border-slate-800/60 dark:hover:bg-blue-500/10"
            :class="isOverdue(task) ? 'border-l-red-500' : isDueSoon(task) ? 'border-l-amber-400' : 'border-l-transparent'"
            @click="openEdit(task)"
          >
            <div class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-100 dark:bg-slate-800">
              <UIcon name="i-heroicons-check-circle" class="h-4 w-4 text-gray-400 dark:text-slate-500" />
            </div>

            <div class="min-w-0 flex-1">
              <span class="truncate text-sm font-semibold text-slate-800 dark:text-slate-100">{{ task.title }}</span>
              <p v-if="task.description" class="mt-0.5 truncate text-xs text-gray-500 dark:text-slate-400">{{ task.description }}</p>

              <div class="mt-1.5 flex flex-wrap items-center gap-2">
                <span
                  v-for="(chip, idx) in referenceChips(task)"
                  :key="idx"
                  class="flex items-center gap-1 rounded-md bg-gray-100 px-2 py-0.5 text-[11px] text-gray-500 dark:bg-slate-800 dark:text-slate-400"
                >
                  <UIcon :name="chip.icon" class="h-3 w-3" />
                  {{ chip.label }}
                </span>
                <span
                  v-if="task.due_date"
                  class="flex items-center gap-1 text-[11px]"
                  :class="isOverdue(task) ? 'font-medium text-red-500' : isDueSoon(task) ? 'font-medium text-amber-600 dark:text-amber-400' : 'text-gray-400 dark:text-slate-500'"
                >
                  <UIcon name="i-heroicons-calendar" class="h-3 w-3" />
                  {{ isOverdue(task) ? 'Overdue' : 'Due' }} {{ formatDate(task.due_date) }}
                </span>
              </div>

              <div class="mt-2 flex items-center gap-2">
                <UDropdownMenu
                  :items="taskStatusOptions.map(opt => ({ label: opt.label, onSelect: () => quickStatusChange(task, opt.value) }))"
                  @click.stop
                >
                  <span
                    class="inline-flex cursor-pointer items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium transition-opacity hover:opacity-80"
                    :class="statusBadgeClass[task.status]"
                  >
                    {{ statusLabels[task.status] }}
                    <UIcon name="i-heroicons-chevron-down" class="h-3 w-3" />
                  </span>
                </UDropdownMenu>
                <span class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium capitalize" :class="priorityBadgeClass[task.priority]">
                  <span class="h-1.5 w-1.5 rounded-full" :class="priorityDotClass[task.priority]" />
                  {{ task.priority }}
                </span>
                <UButton v-if="isAdmin || task.user_id === user?.user_id" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click.stop="deleteTarget = task" />
              </div>
            </div>

            <div class="flex shrink-0 flex-col items-end gap-1">
              <div
                class="flex h-7 w-7 items-center justify-center rounded-full bg-blue-900"
                :title="task.assigned_to ? (userMap[task.assigned_to] ?? 'Unassigned') : 'Unassigned'"
              >
                <span class="text-[10px] font-bold text-blue-200">{{ initials(task.assigned_to) }}</span>
              </div>
            </div>
          </div>
        </template>
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
              {{ group.tasks.length }}
            </span>
          </div>

          <div class="flex-1 space-y-2 overflow-y-auto p-2">
            <div v-if="group.tasks.length === 0" class="py-6 text-center text-xs text-gray-400 dark:text-slate-500">
              No tasks
            </div>

            <div
              v-for="task in group.tasks"
              :key="task.id"
              draggable="true"
              class="cursor-pointer rounded-lg border-l-4 bg-white p-3 shadow-sm ring-1 ring-gray-200 transition-shadow hover:ring-blue-300 dark:bg-slate-900 dark:ring-slate-700"
              :class="isOverdue(task) ? 'border-l-red-500' : isDueSoon(task) ? 'border-l-amber-400' : 'border-l-transparent'"
              @dragstart="onDragStart(task)"
              @dragend="dragOverStatus = null"
              @click="openEdit(task)"
            >
              <div class="flex items-start justify-between gap-2">
                <span class="line-clamp-2 text-sm font-semibold text-slate-800 dark:text-slate-100">{{ task.title }}</span>
                <div
                  class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-900"
                  :title="task.assigned_to ? (userMap[task.assigned_to] ?? 'Unassigned') : 'Unassigned'"
                >
                  <span class="text-[9px] font-bold text-blue-200">{{ initials(task.assigned_to) }}</span>
                </div>
              </div>

              <div v-if="referenceChips(task).length" class="mt-2 flex flex-wrap items-center gap-1">
                <span
                  v-for="(chip, idx) in referenceChips(task).slice(0, 2)"
                  :key="idx"
                  class="flex items-center gap-1 rounded-md bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500 dark:bg-slate-800 dark:text-slate-400"
                >
                  <UIcon :name="chip.icon" class="h-3 w-3" />
                  {{ chip.label }}
                </span>
                <span v-if="referenceChips(task).length > 2" class="text-[10px] text-gray-400 dark:text-slate-500">
                  +{{ referenceChips(task).length - 2 }}
                </span>
              </div>

              <div class="mt-2 flex items-center justify-between gap-2">
                <span class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium capitalize" :class="priorityBadgeClass[task.priority]">
                  <span class="h-1.5 w-1.5 rounded-full" :class="priorityDotClass[task.priority]" />
                  {{ task.priority }}
                </span>
                <span
                  v-if="task.due_date"
                  class="flex items-center gap-1 text-[10px]"
                  :class="isOverdue(task) ? 'font-medium text-red-500' : isDueSoon(task) ? 'font-medium text-amber-600 dark:text-amber-400' : 'text-gray-400 dark:text-slate-500'"
                >
                  <UIcon name="i-heroicons-calendar" class="h-3 w-3" />
                  {{ formatDate(task.due_date) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </UCard>

    <!-- Create / Edit Modal -->
    <UModal v-model:open="showModal" :ui="{ content: 'max-w-2xl' }">
      <template #content>
        <div class="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-xl bg-white shadow-xl dark:bg-slate-900">
          <div class="flex shrink-0 items-start gap-4 border-b border-gray-100 px-6 py-5 dark:border-slate-800">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50 dark:bg-primary-500/10">
              <UIcon name="i-heroicons-check-circle" class="h-5 w-5 text-primary-500" />
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">{{ isEditing ? "Edit Task" : "New Task" }}</h3>
              <p class="mt-0.5 text-sm text-gray-500 dark:text-slate-400">{{ isEditing ? "Update task details" : "Fill in the details to create a new task" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>

          <div class="flex-1 overflow-y-auto px-6 py-5 space-y-5">
            <div class="grid grid-cols-2 gap-x-5 gap-y-4">
              <UFormField label="Title" class="col-span-2" required>
                <UInput v-model="form.title" placeholder="e.g. Replace forklift battery" class="w-full" />
              </UFormField>
              <UFormField label="Description" class="col-span-2">
                <UTextarea v-model="form.description" :rows="3" class="w-full" />
              </UFormField>
              <UFormField label="Status">
                <USelect v-model="form.status" :items="taskStatusOptions" class="w-full" />
              </UFormField>
              <UFormField label="Priority">
                <USelect v-model="form.priority" :items="taskPriorityOptions" class="w-full" />
              </UFormField>
              <UFormField label="Due Date">
                <UInput v-model="form.due_date" type="date" class="w-full" />
              </UFormField>
              <UFormField label="Assignee">
                <USelect v-if="isAdmin" v-model="form.assigned_to" :items="userOptions" placeholder="Assign to…" class="w-full" />
                <div v-else class="flex h-8 items-center rounded-md bg-slate-50 px-3 text-sm text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                  {{ form.assigned_to && form.assigned_to !== user?.user_id ? (userMap[form.assigned_to] ?? "—") : "Assigned to me" }}
                </div>
              </UFormField>
            </div>

            <div class="border-t border-gray-100 pt-4 dark:border-slate-800">
              <p class="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400 dark:text-slate-500">References</p>
              <div class="grid grid-cols-2 gap-x-5 gap-y-4">
                <UFormField label="Asset"><USelect v-model="form.asset_id" :items="assetOptions" placeholder="None" class="w-full" /></UFormField>
                <UFormField label="Work Order"><USelect v-model="form.work_order_id" :items="workOrderOptions" placeholder="None" class="w-full" /></UFormField>
                <UFormField label="Inspection"><USelect v-model="form.inspection_id" :items="inspectionOptions" placeholder="None" class="w-full" /></UFormField>
                <UFormField label="Downtime"><USelect v-model="form.downtime_id" :items="downtimeOptions" placeholder="None" class="w-full" /></UFormField>
                <UFormField label="Issue"><USelect v-model="form.issue_id" :items="issueOptions" placeholder="None" class="w-full" /></UFormField>
                <UFormField label="Purchase Order"><USelect v-model="form.po_no" :items="poOptions" placeholder="None" class="w-full" /></UFormField>
                <UFormField label="Invoice"><USelect v-model="form.invoice_id" :items="invoiceOptions" placeholder="None" class="w-full" /></UFormField>
              </div>
            </div>

            <UAlert v-if="formError" color="error" variant="soft" :description="formError" />
          </div>

          <div class="flex shrink-0 items-center justify-end gap-3 border-t border-gray-100 px-6 py-4 dark:border-slate-800">
            <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
            <UButton :loading="saving" leading-icon="i-heroicons-check" @click="save">{{ isEditing ? "Save Changes" : "Create Task" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Task</h3></template>
          <p class="text-sm text-gray-600 dark:text-slate-300">
            Delete task <strong>"{{ deleteTarget?.title }}"</strong>? This cannot be undone.
          </p>
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
