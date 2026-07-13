<script setup lang="ts">
import type { Inspection, InspectionResult, InspectionTemplateItem } from "~/types"

const { isAdmin } = useAuth()
const { getAll, getOne, create, update, remove, getTemplates, getItemsByTemplate, getResultsByInspection, createResult, updateResult } = useInspections()
const { getAll: getAssets } = useAssets()

const { data: inspections, refresh } = await useAsyncData("inspections", () => getAll())
const { data: templates } = await useAsyncData("insp-templates", () => getTemplates())
const { data: assets } = await useAsyncData("assets-select", () => getAssets())

const resultColors: Record<string, string> = { pass: "success", fail: "error", na: "neutral" }

function fmtDate(v?: string | null) {
  if (!v) return "—"
  const [y, m, d] = v.slice(0, 10).split("-").map(Number)
  return new Date(y, m - 1, d).toLocaleDateString()
}

const assetOptions = computed(() => (assets.value ?? []).map((a) => ({ label: `${a.asset_id} — ${a.manufacturer}`, value: a.asset_id })))
const templateOptions = computed(() => (templates.value ?? []).map((t) => ({ label: t.name, value: t.id })))
const resultOptions = ["pass", "fail", "na"]

const search = ref("")
const resultFilter = ref<string | null>(null)
const resultOptions2 = [{ label: "All", value: null }, ...resultOptions.map((r) => ({ label: r, value: r }))]

const filtered = computed(() =>
  (inspections.value ?? []).filter((i) => {
    const q = search.value.toLowerCase()
    const matchSearch = !q || (i.asset_id ?? "").toLowerCase().includes(q) || i.inspection_no.toLowerCase().includes(q)
    const matchResult = !resultFilter.value || i.overall_result === resultFilter.value
    return matchSearch && matchResult
  })
)

// ── Form modal ───────────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)
const activeTab = ref<"details" | "checklist" | "summary">("details")

const defaultForm = (): Partial<Inspection> => ({
  overall_result: "pass",
  submitted: false,
  inspection_date: new Date().toISOString().slice(0, 10),
})
const form = ref<Partial<Inspection>>(defaultForm())

// ── Checklist state ──────────────────────────────────────────
const checklistItems = ref<InspectionTemplateItem[]>([])
const checklistResults = ref<Record<number, { result: string; notes: string; id?: number }>>({})
const loadingChecklist = ref(false)

async function loadChecklist(templateId: number, inspectionId?: number) {
  loadingChecklist.value = true
  try {
    const items = await getItemsByTemplate(templateId)
    checklistItems.value = items ?? []
    const results: Record<number, { result: string; notes: string; id?: number }> = {}
    for (const item of items ?? []) {
      if (item.id != null) results[item.id] = { result: "na", notes: "" }
    }
    if (inspectionId) {
      const existing = await getResultsByInspection(inspectionId)
      for (const r of existing ?? []) {
        if (r.template_item_id != null) {
          results[r.template_item_id] = { result: r.result, notes: r.notes ?? "", id: r.id }
        }
      }
    }
    checklistResults.value = results
  } finally {
    loadingChecklist.value = false
  }
}

watch(() => form.value.template_id, (tid) => {
  if (tid) loadChecklist(tid, editId.value ?? undefined)
  else { checklistItems.value = []; checklistResults.value = {} }
})

const checklistByCategory = computed(() => {
  const groups: Record<string, InspectionTemplateItem[]> = {}
  for (const item of checklistItems.value) {
    const cat = item.category || "General"
    if (!groups[cat]) groups[cat] = []
    groups[cat].push(item)
  }
  return groups
})

const summaryStats = computed(() => {
  const vals = Object.values(checklistResults.value)
  return {
    pass: vals.filter(r => r.result === "pass").length,
    fail: vals.filter(r => r.result === "fail").length,
    na:   vals.filter(r => r.result === "na").length,
    total: vals.length,
  }
})

const failedItems = computed(() =>
  checklistItems.value.filter(item => item.id != null && checklistResults.value[item.id!]?.result === "fail")
)

function openCreate() {
  form.value = defaultForm()
  isEditing.value = false
  editId.value = null
  formError.value = null
  activeTab.value = "details"
  checklistItems.value = []
  checklistResults.value = {}
  showModal.value = true
}

async function openEdit(id: number) {
  const insp = await getOne(id)
  form.value = { ...insp }
  isEditing.value = true
  editId.value = id
  formError.value = null
  activeTab.value = "details"
  checklistItems.value = []
  checklistResults.value = {}
  if (insp.template_id) await loadChecklist(insp.template_id, id)
  showModal.value = true
}

async function save() {
  saving.value = true
  formError.value = null
  try {
    let inspId: number
    if (isEditing.value && editId.value) {
      await update(editId.value, form.value as Inspection)
      inspId = editId.value
    } else {
      const created = await create(form.value as Inspection)
      inspId = created.id!
    }
    for (const [itemId, res] of Object.entries(checklistResults.value)) {
      const payload: InspectionResult = {
        inspection_id: inspId,
        template_item_id: Number(itemId),
        result: res.result as any,
        notes: res.notes || undefined,
      }
      if (res.id) await updateResult(res.id, payload)
      else await createResult(payload)
    }
    await refresh()
    showModal.value = false
  } catch (e: unknown) {
    formError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    saving.value = false
  }
}

// ── Print checklist ───────────────────────────────────────────
function printChecklist() {
  const insp = form.value
  const items = checklistItems.value
  const results = checklistResults.value

  const groups = checklistByCategory.value
  let rows = ""
  let rowNum = 1
  for (const [cat, catItems] of Object.entries(groups)) {
    rows += `<tr><td colspan="5" style="background:#eff6ff;color:#1d4ed8;font-weight:bold;padding:6px 10px;font-size:11px;letter-spacing:.05em;text-transform:uppercase">${cat}</td></tr>`
    for (const item of catItems) {
      const tickBox = `<span style="display:inline-block;width:11px;height:11px;border:1.5px solid #475569;border-radius:2px;vertical-align:middle;margin-right:3px"></span>`
      rows += `<tr>
        <td style="padding:6px 10px;border-bottom:1px solid #e2e8f0;color:#64748b">${rowNum++}</td>
        <td style="padding:6px 10px;border-bottom:1px solid #e2e8f0">${item.question}${item.is_critical ? ' <span style="color:#dc2626;font-weight:bold" title="Critical">*</span>' : ""}</td>
        <td style="padding:6px 10px;border-bottom:1px solid #e2e8f0;text-align:center">${item.is_critical ? '<span style="color:#dc2626;font-size:10px;font-weight:bold">YES</span>' : "—"}</td>
        <td style="padding:6px 10px;border-bottom:1px solid #e2e8f0">
          <span style="display:inline-flex;gap:10px;font-size:10px;align-items:center">
            <span>${tickBox} Pass</span>
            <span>${tickBox} Fail</span>
            <span>${tickBox} N/A</span>
          </span>
        </td>
        <td style="padding:6px 10px;border-bottom:1px solid #e2e8f0;color:#64748b;font-size:10px">${item.notes || ""}</td>
      </tr>`
    }
  }

  const html = `<!DOCTYPE html><html><head><title>Inspection Checklist – ${insp.inspection_no ?? ""}</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: Arial, sans-serif; font-size: 12px; color: #1e293b; margin: 24px; }
    h1 { color: #2563eb; font-size: 18px; margin: 0 0 4px; }
    .meta { display: flex; gap: 24px; color: #64748b; font-size: 11px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 2px solid #e2e8f0; }
    .meta b { color: #1e293b; }
    table { width: 100%; border-collapse: collapse; }
    thead tr { background: #2563eb; }
    thead th { color: white; padding: 7px 10px; text-align: left; font-size: 11px; }
    tbody tr:nth-child(even) { background: #f8fafc; }
    .result-options { display: flex; gap: 10px; align-items: center; font-size: 10px; }
    .result-options span { display: inline-flex; align-items: center; gap: 3px; white-space: nowrap; }
    .tick-box { display: inline-block; width: 11px; height: 11px; border: 1.5px solid #475569; border-radius: 2px; flex-shrink: 0; }
    .footer { margin-top: 20px; padding: 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; display: flex; gap: 20px; align-items: center; }
    .sig-block { margin-top: 28px; display: flex; gap: 40px; }
    .sig-line { flex: 1; border-top: 1px solid #94a3b8; padding-top: 4px; font-size: 10px; color: #94a3b8; }
    .stamp { color: #94a3b8; font-size: 10px; margin-top: 8px; }
    @media print { body { margin: 12px; } }
  </style></head><body>
  <h1>Inspection Checklist</h1>
  <div class="meta">
    <div>Inspection No: <b>${insp.inspection_no ?? "—"}</b></div>
    <div>Asset: <b>${insp.asset_id ?? "—"}</b></div>
    <div>Date: <b>${insp.inspection_date ?? "—"}</b></div>
    <div>Status: <b>${insp.submitted ? "Submitted" : "Draft"}</b></div>
  </div>
  <table>
    <thead><tr><th style="width:36px">#</th><th>Inspection Item</th><th style="width:72px;text-align:center">Critical</th><th style="width:150px">Result</th><th>Notes</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>
  <div class="footer">
    <div style="color:#64748b;font-size:11px">Overall Result: &nbsp;
      <span style="display:inline-flex;gap:14px;font-size:11px">
        <span><span style="display:inline-block;width:12px;height:12px;border:1.5px solid #475569;border-radius:2px;vertical-align:middle;margin-right:3px"></span> Pass</span>
        <span><span style="display:inline-block;width:12px;height:12px;border:1.5px solid #475569;border-radius:2px;vertical-align:middle;margin-right:3px"></span> Fail</span>
        <span><span style="display:inline-block;width:12px;height:12px;border:1.5px solid #475569;border-radius:2px;vertical-align:middle;margin-right:3px"></span> N/A</span>
      </span>
    </div>
  </div>
  <div class="sig-block">
    <div class="sig-line">Inspected by</div>
    <div class="sig-line">Signature</div>
    <div class="sig-line">Date</div>
  </div>
  ${insp.notes ? `<div style="margin-top:12px;font-size:11px;color:#64748b"><b>Notes:</b> ${insp.notes}</div>` : ""}
  <div class="stamp">Generated ${new Date().toLocaleString()}</div>
  </body></html>`

  const win = window.open("", "_blank", "width=860,height=700")
  if (win) {
    win.document.write(html)
    win.document.close()
    win.focus()
    setTimeout(() => win.print(), 400)
  }
}

// ── Delete modal ─────────────────────────────────────────────
const deleteTarget = ref<Inspection | null>(null)
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
</script>

<template>
  <div class="flex min-h-full flex-col gap-4">
    <UCard :ui="{ root: 'flex flex-col flex-1 min-h-0', body: 'flex flex-col flex-1 min-h-0 p-0' }">
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <div class="flex flex-wrap gap-3">
            <UInput v-model="search" placeholder="Search by asset or inspection no..." leading-icon="i-heroicons-magnifying-glass" class="max-w-xs" />
            <USelect v-model="resultFilter" :items="resultOptions2" placeholder="Filter by result" class="w-40" />
          </div>
          <UButton leading-icon="i-heroicons-plus" @click="openCreate" class="!bg-blue-700 hover:!bg-blue-800">New Inspection</UButton>
        </div>
      </template>

      <!-- Inspection card list -->
      <div class="overflow-auto h-full p-4 space-y-2">
        <div v-if="filtered.length === 0" class="py-12 text-center text-sm text-gray-400">
          No inspections found.
        </div>
        <div
          v-for="insp in filtered"
          :key="insp.id"
          class="flex cursor-pointer items-start gap-4 rounded-lg px-5 py-4 ring-1 ring-gray-200 hover:bg-blue-50/40 transition-colors border-l-4"
          :class="insp.overall_result === 'fail' ? 'border-l-red-400' : 'border-l-transparent'"
          @click="openEdit(insp.id)"
        >
          <!-- Left icon -->
          <div class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gray-100">
            <UIcon name="i-heroicons-magnifying-glass" class="h-4 w-4 text-gray-400" />
          </div>

          <!-- Main content -->
          <div class="min-w-0 flex-1">
            <!-- Title -->
            <div class="flex items-center gap-2">
              <span class="text-sm font-semibold text-slate-800">{{ insp.inspection_no }}</span>
            </div>
            <!-- Asset -->
            <p class="mt-0.5 text-xs text-gray-500">Asset: {{ insp.asset_id ?? "—" }}</p>
            <!-- Meta row -->
            <div class="mt-1.5 flex flex-wrap items-center gap-2">
              <span class="flex items-center gap-1 text-[11px] text-gray-400">
                <UIcon name="i-heroicons-calendar" class="h-3 w-3" />
                {{ fmtDate(insp.inspection_date) }}
              </span>
            </div>
          </div>

          <!-- Right side -->
          <div class="shrink-0 flex flex-col items-end gap-2">
            <UBadge :color="resultColors[insp.overall_result] ?? 'neutral'" variant="soft" size="xs" class="capitalize">{{ insp.overall_result }}</UBadge>
            <UBadge :color="insp.submitted ? 'success' : 'neutral'" variant="soft" size="xs">{{ insp.submitted ? "Submitted" : "Draft" }}</UBadge>
            <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click.stop="deleteTarget = insp" />
          </div>
        </div>
      </div>
    </UCard>

    <!-- Inspection Modal -->
    <UModal v-model:open="showModal">
      <template #content>
        <div class="flex max-h-[90vh] w-full max-w-3xl flex-col rounded-xl bg-white shadow-xl">

          <!-- Header -->
          <div class="flex shrink-0 items-center gap-4 border-b border-slate-100 px-6 py-4">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50">
              <UIcon name="i-heroicons-magnifying-glass" class="h-5 w-5 text-blue-600" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900">{{ isEditing ? "Edit Inspection" : "New Inspection" }}</h3>
              <p class="text-xs text-slate-500">{{ form.inspection_no || "—" }} {{ form.asset_id ? `· ${form.asset_id}` : "" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>

          <!-- Tabs -->
          <div class="shrink-0 border-b border-slate-100 px-6">
            <div class="flex gap-1">
              <button
                v-for="tab in [{ id: 'details', label: 'Inspection Details', icon: 'i-heroicons-clipboard-document' }, { id: 'checklist', label: 'Checklist', icon: 'i-heroicons-check-circle' }, { id: 'summary', label: 'Summary', icon: 'i-heroicons-chart-bar' }]"
                :key="tab.id"
                class="flex items-center gap-1.5 border-b-2 px-3 py-3 text-xs font-medium transition-colors"
                :class="activeTab === tab.id ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'"
                @click="activeTab = tab.id as any"
              >
                <UIcon :name="tab.icon" class="h-3.5 w-3.5" />
                {{ tab.label }}
                <span v-if="tab.id === 'checklist' && checklistItems.length" class="ml-1 rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] text-slate-500">{{ checklistItems.length }}</span>
              </button>
            </div>
          </div>

          <!-- Tab content -->
          <div class="flex-1 overflow-y-auto px-6 py-5">

            <!-- Details tab -->
            <div v-if="activeTab === 'details'" class="grid grid-cols-2 gap-x-5 gap-y-4">
              <UFormField label="Inspection No" class="col-span-2">
                <UInput
                  :model-value="isEditing ? form.inspection_no : 'Auto-generated on save'"
                  disabled
                  class="w-full"
                />
              </UFormField>
              <UFormField label="Asset">
                <USelect v-model="form.asset_id" :items="assetOptions" placeholder="Select asset" class="w-full" />
              </UFormField>
              <UFormField label="Template">
                <USelect v-model="form.template_id" :items="templateOptions" placeholder="Select template" class="w-full" />
              </UFormField>
              <UFormField label="Inspection Date" required>
                <UInput v-model="form.inspection_date" type="date" class="w-full" />
              </UFormField>
              <UFormField label="Inspection Time">
                <UInput v-model="form.inspection_time" type="time" class="w-full" />
              </UFormField>
            </div>

            <!-- Checklist tab -->
            <div v-else-if="activeTab === 'checklist'">
              <div v-if="!form.template_id" class="flex flex-col items-center justify-center py-12 text-slate-400">
                <UIcon name="i-heroicons-clipboard-document" class="mb-2 h-10 w-10 opacity-30" />
                <p class="text-sm">Select a template on the Details tab to load checklist items.</p>
              </div>
              <div v-else-if="loadingChecklist" class="flex items-center justify-center py-12 text-slate-400">
                <UIcon name="i-heroicons-arrow-path" class="mr-2 h-5 w-5 animate-spin" /> Loading checklist…
              </div>
              <div v-else-if="!checklistItems.length" class="flex flex-col items-center justify-center py-12 text-slate-400">
                <p class="text-sm">No items found for this template.</p>
              </div>
              <div v-else class="space-y-6">
                <div v-for="(items, category) in checklistByCategory" :key="category">
                  <h4 class="mb-2 text-[10px] font-semibold uppercase tracking-wider text-blue-600">{{ category }}</h4>
                  <div class="overflow-hidden rounded-lg border border-slate-200">
                    <table class="w-full text-xs">
                      <thead>
                        <tr class="bg-slate-50 text-left text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                          <th class="px-3 py-2 w-8">#</th>
                          <th class="px-3 py-2">Item</th>
                          <th class="px-3 py-2 w-24 text-center">Result</th>
                          <th class="px-3 py-2">Notes</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="(item, idx) in items" :key="item.id" class="border-t border-slate-100">
                          <td class="px-3 py-2 text-slate-400">{{ idx + 1 }}</td>
                          <td class="px-3 py-2">
                            <span :class="item.is_critical ? 'font-semibold text-slate-800' : 'text-slate-700'">{{ item.question }}</span>
                            <span v-if="item.is_critical" class="ml-1 text-red-500 text-[10px] font-bold" title="Critical">★</span>
                          </td>
                          <td class="px-3 py-2">
                            <USelect
                              v-if="item.id != null"
                              v-model="checklistResults[item.id!].result"
                              :items="resultOptions"
                              size="xs"
                              class="w-full"
                            />
                          </td>
                          <td class="px-3 py-2">
                            <UInput
                              v-if="item.id != null"
                              v-model="checklistResults[item.id!].notes"
                              placeholder="Notes…"
                              size="xs"
                              class="w-full"
                            />
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>

            <!-- Summary tab -->
            <div v-else-if="activeTab === 'summary'" class="space-y-5">
              <!-- Stats -->
              <div v-if="checklistItems.length" class="grid grid-cols-3 gap-3">
                <div class="rounded-lg bg-green-50 px-4 py-3 text-center ring-1 ring-green-200">
                  <p class="text-2xl font-bold text-green-600">{{ summaryStats.pass }}</p>
                  <p class="text-xs text-green-700">Pass</p>
                </div>
                <div class="rounded-lg bg-red-50 px-4 py-3 text-center ring-1 ring-red-200">
                  <p class="text-2xl font-bold text-red-600">{{ summaryStats.fail }}</p>
                  <p class="text-xs text-red-700">Fail</p>
                </div>
                <div class="rounded-lg bg-slate-50 px-4 py-3 text-center ring-1 ring-slate-200">
                  <p class="text-2xl font-bold text-slate-500">{{ summaryStats.na }}</p>
                  <p class="text-xs text-slate-500">N/A</p>
                </div>
              </div>

              <!-- Failed items -->
              <div v-if="failedItems.length">
                <p class="mb-2 text-xs font-semibold text-red-600">Failed Items ({{ failedItems.length }})</p>
                <ul class="space-y-1">
                  <li v-for="item in failedItems" :key="item.id" class="flex items-start gap-2 rounded bg-red-50 px-3 py-1.5 text-xs text-red-700">
                    <UIcon name="i-heroicons-x-circle" class="mt-0.5 h-3.5 w-3.5 shrink-0" />
                    <span>{{ item.question }}</span>
                    <span v-if="item.is_critical" class="ml-auto shrink-0 font-bold text-red-500">Critical</span>
                  </li>
                </ul>
              </div>

              <!-- Overall result & notes -->
              <div class="grid grid-cols-2 gap-x-5 gap-y-4">
                <UFormField label="Overall Result">
                  <USelect v-model="form.overall_result" :items="resultOptions" class="w-full" />
                </UFormField>
                <UFormField label="Submitted">
                  <div class="flex h-full items-center">
                    <UCheckbox v-model="form.submitted" label="Mark as submitted" />
                  </div>
                </UFormField>
                <UFormField label="Notes" class="col-span-2">
                  <UTextarea v-model="form.notes" :rows="3" class="w-full" />
                </UFormField>
              </div>

            </div>
          </div>

          <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="mx-6 mb-2 shrink-0" />

          <!-- Footer -->
          <div class="flex shrink-0 items-center justify-between border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" leading-icon="i-heroicons-printer" color="neutral" :disabled="!checklistItems.length" @click="printChecklist">
              Print Checklist
            </UButton>
            <div class="flex gap-3">
              <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
              <UButton :loading="saving" @click="save">{{ isEditing ? "Save Changes" : "Create Inspection" }}</UButton>
            </div>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Inspection</h3></template>
          <p class="text-sm text-slate-500">Delete inspection <strong>{{ deleteTarget?.inspection_no }}</strong>? This cannot be undone.</p>
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
