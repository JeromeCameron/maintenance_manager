<script setup lang="ts">
import type { Holiday, AssetModel, DowntimeCause, PartCategory, InspectionTemplate, InspectionTemplateItem, PmPlans } from "~/types"

const { getAll: getHolidays, create: createHoliday, update: updateHoliday, remove: removeHoliday } = useHolidays()
const { getAll: getModels, getOne: getModel, create: createModel, update: updateModel, remove: removeModel } = useAssetModels()
const { getCauses, createCause, updateCause, removeCause } = useDowntime()
const { getCategories, createCategory, updateCategory, removeCategory } = useInventory()
const { getTemplates, createTemplate, updateTemplate, removeTemplate, getItemsByTemplate, createItem, updateItem, removeItem } = useInspections()
const { getPlans, createPlan, updatePlan, removePlan } = useMaintenance()

const activeTab = ref("holidays")
const tabs = [
  { value: "holidays", slot: "holidays", label: "Holidays", icon: "i-heroicons-calendar-days" },
  { value: "asset-models", slot: "asset-models", label: "Asset Models", icon: "i-heroicons-cube" },
  { value: "downtime-causes", slot: "downtime-causes", label: "Downtime Causes", icon: "i-heroicons-exclamation-triangle" },
  { value: "part-categories", slot: "part-categories", label: "Part Categories", icon: "i-heroicons-tag" },
  { value: "inspection-templates", slot: "inspection-templates", label: "Inspection Templates", icon: "i-heroicons-clipboard-document-check" },
  { value: "pm-plans", slot: "pm-plans", label: "PM Plans", icon: "i-heroicons-wrench-screwdriver" },
]

// ── Holidays ─────────────────────────────────────────────────
const { data: holidays, refresh: refreshHolidays } = await useAsyncData("settings-holidays", () => getHolidays())

const holidayColumns = [
  { accessorKey: "name", header: "Name" },
  { accessorKey: "holiday_date", header: "Date" },
  { id: "actions", header: "" },
]

const showHolidayModal = ref(false)
const holidayEditing = ref<Holiday | null>(null)
const holidayForm = ref<Partial<Holiday>>({})
const savingHoliday = ref(false)
const holidayError = ref<string | null>(null)

function openCreateHoliday() {
  holidayEditing.value = null
  holidayForm.value = {}
  holidayError.value = null
  showHolidayModal.value = true
}

function openEditHoliday(row: Holiday) {
  holidayEditing.value = row
  holidayForm.value = { ...row }
  holidayError.value = null
  showHolidayModal.value = true
}

async function saveHoliday() {
  savingHoliday.value = true
  holidayError.value = null
  try {
    if (holidayEditing.value?.holiday_id) {
      await updateHoliday(holidayEditing.value.holiday_id, holidayForm.value as Holiday)
    } else {
      await createHoliday(holidayForm.value as Holiday)
    }
    await refreshHolidays()
    showHolidayModal.value = false
  } catch (e: unknown) {
    holidayError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingHoliday.value = false
  }
}

const deleteHolidayTarget = ref<Holiday | null>(null)
const deletingHoliday = ref(false)
const showDeleteHolidayModal = computed({
  get: () => !!deleteHolidayTarget.value,
  set: (v) => { if (!v) deleteHolidayTarget.value = null },
})

async function confirmDeleteHoliday() {
  if (!deleteHolidayTarget.value?.holiday_id) return
  deletingHoliday.value = true
  try {
    await removeHoliday(deleteHolidayTarget.value.holiday_id)
    await refreshHolidays()
    deleteHolidayTarget.value = null
  } finally {
    deletingHoliday.value = false
  }
}

// ── Asset Models ─────────────────────────────────────────────
const { data: models, refresh: refreshModels } = await useAsyncData("settings-models", () => getModels())

const modelColumns = [
  { accessorKey: "model_no", header: "Model No." },
  { accessorKey: "manufacturer", header: "Manufacturer" },
  { accessorKey: "category", header: "Category" },
  { accessorKey: "description", header: "Description" },
  { id: "actions", header: "" },
]

const categoryOptions = ["baler", "conveyor", "bobcat", "forklift", "scale"]
const showModelModal = ref(false)
const modelEditing = ref<AssetModel | null>(null)
const modelForm = ref<Partial<AssetModel>>({})
const savingModel = ref(false)
const modelError = ref<string | null>(null)

function openCreateModel() {
  modelEditing.value = null
  modelForm.value = {}
  modelError.value = null
  showModelModal.value = true
}

async function openEditModel(row: AssetModel) {
  modelEditing.value = row
  modelForm.value = { ...await getModel(row.model_no) }
  modelError.value = null
  showModelModal.value = true
}

async function saveModel() {
  savingModel.value = true
  modelError.value = null
  try {
    if (modelEditing.value) {
      await updateModel(modelEditing.value.model_no, modelForm.value as AssetModel)
    } else {
      await createModel(modelForm.value as AssetModel)
    }
    await refreshModels()
    showModelModal.value = false
  } catch (e: unknown) {
    modelError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingModel.value = false
  }
}

const deleteModelTarget = ref<AssetModel | null>(null)
const deletingModel = ref(false)
const showDeleteModelModal = computed({
  get: () => !!deleteModelTarget.value,
  set: (v) => { if (!v) deleteModelTarget.value = null },
})

async function confirmDeleteModel() {
  if (!deleteModelTarget.value) return
  deletingModel.value = true
  try {
    await removeModel(deleteModelTarget.value.model_no)
    await refreshModels()
    deleteModelTarget.value = null
  } finally {
    deletingModel.value = false
  }
}

// ── Downtime Causes ──────────────────────────────────────────
const { data: causes, refresh: refreshCauses } = await useAsyncData("settings-causes", () => getCauses())

const causeColumns = [
  { accessorKey: "name", header: "Name" },
  { accessorKey: "description", header: "Description" },
  { accessorKey: "active", header: "Active" },
  { id: "actions", header: "" },
]

const showCauseModal = ref(false)
const causeEditing = ref<DowntimeCause | null>(null)
const causeForm = ref<Partial<DowntimeCause>>({ active: true })
const savingCause = ref(false)
const causeError = ref<string | null>(null)

function openCreateCause() {
  causeEditing.value = null
  causeForm.value = { active: true }
  causeError.value = null
  showCauseModal.value = true
}

function openEditCause(row: DowntimeCause) {
  causeEditing.value = row
  causeForm.value = { ...row }
  causeError.value = null
  showCauseModal.value = true
}

async function saveCause() {
  savingCause.value = true
  causeError.value = null
  try {
    if (causeEditing.value?.cause_id) {
      await updateCause(causeEditing.value.cause_id, causeForm.value as DowntimeCause)
    } else {
      await createCause(causeForm.value as DowntimeCause)
    }
    await refreshCauses()
    showCauseModal.value = false
  } catch (e: unknown) {
    causeError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingCause.value = false
  }
}

const deleteCauseTarget = ref<DowntimeCause | null>(null)
const deletingCause = ref(false)
const showDeleteCauseModal = computed({
  get: () => !!deleteCauseTarget.value,
  set: (v) => { if (!v) deleteCauseTarget.value = null },
})

async function confirmDeleteCause() {
  if (!deleteCauseTarget.value?.cause_id) return
  deletingCause.value = true
  try {
    await removeCause(deleteCauseTarget.value.cause_id)
    await refreshCauses()
    deleteCauseTarget.value = null
  } finally {
    deletingCause.value = false
  }
}

// ── Part Categories ──────────────────────────────────────────
const { data: categories, refresh: refreshCategories } = await useAsyncData("settings-categories", () => getCategories())

const categoryColumns = [
  { accessorKey: "name", header: "Name" },
  { id: "actions", header: "" },
]

const showCategoryModal = ref(false)
const categoryEditing = ref<PartCategory | null>(null)
const categoryForm = ref<Partial<PartCategory>>({})
const savingCategory = ref(false)
const categoryError = ref<string | null>(null)

function openCreateCategory() {
  categoryEditing.value = null
  categoryForm.value = {}
  categoryError.value = null
  showCategoryModal.value = true
}

function openEditCategory(row: PartCategory) {
  categoryEditing.value = row
  categoryForm.value = { ...row }
  categoryError.value = null
  showCategoryModal.value = true
}

async function saveCategory() {
  savingCategory.value = true
  categoryError.value = null
  try {
    if (categoryEditing.value?.id) {
      await updateCategory(categoryEditing.value.id, categoryForm.value as PartCategory)
    } else {
      await createCategory(categoryForm.value as PartCategory)
    }
    await refreshCategories()
    showCategoryModal.value = false
  } catch (e: unknown) {
    categoryError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingCategory.value = false
  }
}

const deleteCategoryTarget = ref<PartCategory | null>(null)
const deletingCategory = ref(false)
const showDeleteCategoryModal = computed({
  get: () => !!deleteCategoryTarget.value,
  set: (v) => { if (!v) deleteCategoryTarget.value = null },
})

async function confirmDeleteCategory() {
  if (!deleteCategoryTarget.value?.id) return
  deletingCategory.value = true
  try {
    await removeCategory(deleteCategoryTarget.value.id)
    await refreshCategories()
    deleteCategoryTarget.value = null
  } finally {
    deletingCategory.value = false
  }
}

// ── Inspection Templates ──────────────────────────────────────
const { data: templates, refresh: refreshTemplates } = await useAsyncData("settings-templates", () => getTemplates())

const assetTypeOptions = ["baler", "conveyor", "bobcat", "forklift", "scale"]
const frequencyOptions = ["daily", "weekly", "monthly"]

const templateColumns = [
  { accessorKey: "name", header: "Name" },
  { accessorKey: "asset_type", header: "Asset Type" },
  { accessorKey: "frequency", header: "Frequency" },
  { accessorKey: "active", header: "Active" },
  { id: "actions", header: "" },
]

const showTemplateModal = ref(false)
const templateEditing = ref<InspectionTemplate | null>(null)
const templateForm = ref<Partial<InspectionTemplate>>({ active: true })
const savingTemplate = ref(false)
const templateError = ref<string | null>(null)

function openCreateTemplate() {
  templateEditing.value = null
  templateForm.value = { active: true }
  templateError.value = null
  showTemplateModal.value = true
}

function openEditTemplate(row: InspectionTemplate) {
  templateEditing.value = row
  templateForm.value = { ...row }
  templateError.value = null
  showTemplateModal.value = true
}

async function saveTemplate() {
  savingTemplate.value = true
  templateError.value = null
  try {
    if (templateEditing.value?.id) {
      await updateTemplate(templateEditing.value.id, templateForm.value as InspectionTemplate)
    } else {
      await createTemplate(templateForm.value as InspectionTemplate)
    }
    await refreshTemplates()
    showTemplateModal.value = false
  } catch (e: unknown) {
    templateError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingTemplate.value = false
  }
}

const deleteTemplateTarget = ref<InspectionTemplate | null>(null)
const deletingTemplate = ref(false)
const showDeleteTemplateModal = computed({
  get: () => !!deleteTemplateTarget.value,
  set: (v) => { if (!v) deleteTemplateTarget.value = null },
})

async function confirmDeleteTemplate() {
  if (!deleteTemplateTarget.value?.id) return
  deletingTemplate.value = true
  try {
    await removeTemplate(deleteTemplateTarget.value.id)
    await refreshTemplates()
    deleteTemplateTarget.value = null
  } finally {
    deletingTemplate.value = false
  }
}

// ── Template Items (questions) ────────────────────────────────
const showItemsModal = ref(false)
const activeTemplate = ref<InspectionTemplate | null>(null)
const templateItems = ref<InspectionTemplateItem[]>([])
const loadingItems = ref(false)

const itemColumns = [
  { accessorKey: "order", header: "#" },
  { accessorKey: "question", header: "Question" },
  { accessorKey: "category", header: "Category" },
  { accessorKey: "is_critical", header: "Critical" },
  { id: "actions", header: "" },
]

async function openItemsModal(template: InspectionTemplate) {
  activeTemplate.value = template
  loadingItems.value = true
  showItemsModal.value = true
  templateItems.value = await getItemsByTemplate(template.id!)
  loadingItems.value = false
}

const showItemForm = ref(false)
const itemEditing = ref<InspectionTemplateItem | null>(null)
const itemForm = ref<Partial<InspectionTemplateItem>>({ is_critical: false })
const savingItem = ref(false)
const itemError = ref<string | null>(null)

function openCreateItem() {
  itemEditing.value = null
  itemForm.value = { is_critical: false, template_id: activeTemplate.value?.id, order: templateItems.value.length + 1 }
  itemError.value = null
  showItemForm.value = true
}

function openEditItem(row: InspectionTemplateItem) {
  itemEditing.value = row
  itemForm.value = { ...row }
  itemError.value = null
  showItemForm.value = true
}

async function saveItem() {
  savingItem.value = true
  itemError.value = null
  try {
    if (itemEditing.value?.id) {
      const updated = await updateItem(itemEditing.value.id, itemForm.value as InspectionTemplateItem)
      templateItems.value = templateItems.value.map((i) => i.id === updated.id ? updated : i)
    } else {
      const created = await createItem(itemForm.value as InspectionTemplateItem)
      templateItems.value = [...templateItems.value, created]
    }
    showItemForm.value = false
  } catch (e: unknown) {
    itemError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingItem.value = false
  }
}

async function deleteItem(id: number) {
  await removeItem(id)
  templateItems.value = templateItems.value.filter((i) => i.id !== id)
}

// ── PM Plans ──────────────────────────────────────────────────
const { data: pmPlans, refresh: refreshPlans } = await useAsyncData("settings-pm-plans", () => getPlans())

const pmTriggerOptions = ["operating_hours", "calendar_based"]
const pmFrequencyOptions = ["daily", "weekly", "fortnightly", "monthly", "every_other_month", "every_four_month", "quarterly", "biannually", "annually"]
const pmOwnerOptions = ["operator", "maintenance_team", "contractor"]
const assetTypeOptionsForPm = ["baler", "conveyor", "bobcat", "forklift", "scale"]

const pmPlanColumns = [
  { accessorKey: "pm_id", header: "Plan ID" },
  { accessorKey: "asset_type", header: "Asset Type" },
  { accessorKey: "frequency", header: "Frequency" },
  { accessorKey: "trigger", header: "Trigger" },
  { accessorKey: "owner", header: "Owner" },
  { accessorKey: "description", header: "Description" },
  { id: "actions", header: "" },
]

const showPmPlanModal = ref(false)
const pmPlanEditing = ref<PmPlans | null>(null)
const pmPlanForm = ref<Partial<PmPlans>>({})
const savingPmPlan = ref(false)
const pmPlanError = ref<string | null>(null)

function openCreatePmPlan() {
  pmPlanEditing.value = null
  pmPlanForm.value = {}
  pmPlanError.value = null
  showPmPlanModal.value = true
}

function openEditPmPlan(row: PmPlans) {
  pmPlanEditing.value = row
  pmPlanForm.value = { ...row }
  pmPlanError.value = null
  showPmPlanModal.value = true
}

async function savePmPlan() {
  savingPmPlan.value = true
  pmPlanError.value = null
  try {
    if (pmPlanEditing.value) {
      await updatePlan(pmPlanEditing.value.pm_id, pmPlanForm.value as PmPlans)
    } else {
      await createPlan(pmPlanForm.value as PmPlans)
    }
    await refreshPlans()
    showPmPlanModal.value = false
  } catch (e: unknown) {
    pmPlanError.value = (e as { message?: string }).message ?? "Save failed"
  } finally {
    savingPmPlan.value = false
  }
}

const deletePmPlanTarget = ref<PmPlans | null>(null)
const deletingPmPlan = ref(false)
const showDeletePmPlanModal = computed({
  get: () => !!deletePmPlanTarget.value,
  set: (v) => { if (!v) deletePmPlanTarget.value = null },
})

async function confirmDeletePmPlan() {
  if (!deletePmPlanTarget.value) return
  deletingPmPlan.value = true
  try {
    await removePlan(deletePmPlanTarget.value.pm_id)
    await refreshPlans()
    deletePmPlanTarget.value = null
  } finally {
    deletingPmPlan.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-slate-900">Settings</h1>

    <UTabs v-model="activeTab" :items="tabs">
      <template #leading="{ item }">
        <UIcon :name="item.icon" class="h-4 w-4" />
      </template>

      <!-- ── Holidays ── -->
      <template #holidays>
        <div class="mt-4 space-y-4">
          <div class="flex justify-end">
            <UButton leading-icon="i-heroicons-plus" @click="openCreateHoliday">Add Holiday</UButton>
          </div>
          <UCard>
            <UTable :data="holidays ?? []" :columns="holidayColumns">
              <template #actions-cell="{ row: { original: row } }">
                <div class="flex items-center gap-1">
                  <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEditHoliday(row)" />
                  <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteHolidayTarget = row" />
                </div>
              </template>
            </UTable>
          </UCard>
        </div>
      </template>

      <!-- ── Asset Models ── -->
      <template #asset-models>
        <div class="mt-4 space-y-4">
          <div class="flex justify-end">
            <UButton leading-icon="i-heroicons-plus" @click="openCreateModel">Add Model</UButton>
          </div>
          <UCard>
            <UTable :data="models ?? []" :columns="modelColumns">
              <template #category-cell="{ row: { original: row } }">
                <span class="capitalize">{{ row.category ?? "—" }}</span>
              </template>
              <template #description-cell="{ row: { original: row } }">
                <span class="text-slate-500">{{ row.description ?? "—" }}</span>
              </template>
              <template #actions-cell="{ row: { original: row } }">
                <div class="flex items-center gap-1">
                  <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEditModel(row)" />
                  <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteModelTarget = row" />
                </div>
              </template>
            </UTable>
          </UCard>
        </div>
      </template>

      <!-- ── Downtime Causes ── -->
      <template #downtime-causes>
        <div class="mt-4 space-y-4">
          <div class="flex justify-end">
            <UButton leading-icon="i-heroicons-plus" @click="openCreateCause">Add Cause</UButton>
          </div>
          <UCard>
            <UTable :data="causes ?? []" :columns="causeColumns">
              <template #active-cell="{ row: { original: row } }">
                <UBadge :color="row.active ? 'success' : 'neutral'" variant="soft" size="xs">
                  {{ row.active ? "Active" : "Inactive" }}
                </UBadge>
              </template>
              <template #description-cell="{ row: { original: row } }">
                <span class="text-slate-500">{{ row.description ?? "—" }}</span>
              </template>
              <template #actions-cell="{ row: { original: row } }">
                <div class="flex items-center gap-1">
                  <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEditCause(row)" />
                  <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteCauseTarget = row" />
                </div>
              </template>
            </UTable>
          </UCard>
        </div>
      </template>
      <!-- ── Part Categories ── -->
      <template #part-categories>
        <div class="mt-4 space-y-4">
          <div class="flex justify-end">
            <UButton leading-icon="i-heroicons-plus" @click="openCreateCategory">Add Category</UButton>
          </div>
          <UCard>
            <UTable :data="categories ?? []" :columns="categoryColumns">
              <template #actions-cell="{ row: { original: row } }">
                <div class="flex items-center gap-1">
                  <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEditCategory(row)" />
                  <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteCategoryTarget = row" />
                </div>
              </template>
            </UTable>
          </UCard>
        </div>
      </template>

      <!-- ── Inspection Templates ── -->
      <template #inspection-templates>
        <div class="mt-4 space-y-4">
          <div class="flex justify-end">
            <UButton leading-icon="i-heroicons-plus" @click="openCreateTemplate">Add Template</UButton>
          </div>
          <UCard>
            <UTable :data="templates ?? []" :columns="templateColumns">
              <template #active-cell="{ row: { original: row } }">
                <UBadge :color="row.active ? 'success' : 'neutral'" variant="soft" size="xs">
                  {{ row.active ? "Active" : "Inactive" }}
                </UBadge>
              </template>
              <template #asset_type-cell="{ row: { original: row } }">
                <span class="capitalize">{{ row.asset_type }}</span>
              </template>
              <template #actions-cell="{ row: { original: row } }">
                <div class="flex items-center gap-1">
                  <UButton variant="ghost" size="xs" icon="i-heroicons-list-bullet" @click="openItemsModal(row)" />
                  <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEditTemplate(row)" />
                  <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTemplateTarget = row" />
                </div>
              </template>
            </UTable>
          </UCard>
        </div>
      </template>
      <!-- ── PM Plans ── -->
      <template #pm-plans>
        <div class="mt-4 space-y-4">
          <div class="flex justify-end">
            <UButton leading-icon="i-heroicons-plus" @click="openCreatePmPlan">Add PM Plan</UButton>
          </div>
          <UCard>
            <UTable :data="pmPlans ?? []" :columns="pmPlanColumns">
              <template #asset_type-cell="{ row: { original: row } }">
                <span class="capitalize">{{ row.asset_type ?? "—" }}</span>
              </template>
              <template #frequency-cell="{ row: { original: row } }">
                <span class="capitalize">{{ row.frequency?.replace(/_/g, " ") ?? "—" }}</span>
              </template>
              <template #trigger-cell="{ row: { original: row } }">
                <span class="capitalize">{{ row.trigger?.replace(/_/g, " ") ?? "—" }}</span>
              </template>
              <template #owner-cell="{ row: { original: row } }">
                <span class="capitalize">{{ row.owner?.replace(/_/g, " ") ?? "—" }}</span>
              </template>
              <template #description-cell="{ row: { original: row } }">
                <span class="text-slate-500 truncate max-w-xs block">{{ row.description ?? "—" }}</span>
              </template>
              <template #actions-cell="{ row: { original: row } }">
                <div class="flex items-center gap-1">
                  <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEditPmPlan(row)" />
                  <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deletePmPlanTarget = row" />
                </div>
              </template>
            </UTable>
          </UCard>
        </div>
      </template>
    </UTabs>

    <!-- Holiday Modal -->
    <UModal v-model:open="showHolidayModal">
      <template #content>
        <div class="w-full rounded-xl bg-white shadow-xl">
          <div class="flex items-center justify-between border-b border-slate-100 px-6 py-5">
            <h3 class="text-base font-semibold text-slate-900">{{ holidayEditing ? "Edit Holiday" : "Add Holiday" }}</h3>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showHolidayModal = false" />
          </div>
          <div class="space-y-4 px-6 py-5">
            <UFormField label="Name" required>
              <UInput v-model="holidayForm.name" placeholder="e.g. Christmas Day" class="w-full" />
            </UFormField>
            <UFormField label="Date" required>
              <UInput v-model="holidayForm.holiday_date" type="date" class="w-full" />
            </UFormField>
          </div>
          <UAlert v-if="holidayError" color="error" variant="soft" :description="holidayError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showHolidayModal = false">Cancel</UButton>
            <UButton :loading="savingHoliday" @click="saveHoliday">Save</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Holiday Delete Modal -->
    <UModal v-model:open="showDeleteHolidayModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Holiday</h3></template>
          <p class="text-sm text-slate-500">Delete <strong>{{ deleteHolidayTarget?.name }}</strong>? This cannot be undone.</p>
          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton variant="ghost" @click="deleteHolidayTarget = null">Cancel</UButton>
              <UButton color="error" :loading="deletingHoliday" @click="confirmDeleteHoliday">Delete</UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <!-- Asset Model Modal -->
    <UModal v-model:open="showModelModal">
      <template #content>
        <div class="w-full max-w-lg rounded-xl bg-white shadow-xl">
          <div class="flex items-center justify-between border-b border-slate-100 px-6 py-5">
            <h3 class="text-base font-semibold text-slate-900">{{ modelEditing ? `Edit Model: ${modelEditing.model_no}` : "Add Asset Model" }}</h3>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModelModal = false" />
          </div>
          <div class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
            <UFormField label="Model No." required>
              <UInput v-model="modelForm.model_no" placeholder="e.g. HSM-500" :disabled="!!modelEditing" class="w-full" />
            </UFormField>
            <UFormField label="Manufacturer" required>
              <UInput v-model="modelForm.manufacturer" placeholder="e.g. HSM" class="w-full" />
            </UFormField>
            <UFormField label="Category">
              <USelect v-model="modelForm.category" :items="categoryOptions" placeholder="Select category" class="w-full" />
            </UFormField>
            <UFormField label="Description" class="col-span-2">
              <UTextarea v-model="modelForm.description" :rows="3" class="w-full" />
            </UFormField>
          </div>
          <UAlert v-if="modelError" color="error" variant="soft" :description="modelError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showModelModal = false">Cancel</UButton>
            <UButton :loading="savingModel" @click="saveModel">{{ modelEditing ? "Save Changes" : "Create Model" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Asset Model Delete Modal -->
    <UModal v-model:open="showDeleteModelModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Asset Model</h3></template>
          <p class="text-sm text-slate-500">Delete model <strong>{{ deleteModelTarget?.model_no }}</strong>? This cannot be undone.</p>
          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton variant="ghost" @click="deleteModelTarget = null">Cancel</UButton>
              <UButton color="error" :loading="deletingModel" @click="confirmDeleteModel">Delete</UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <!-- Downtime Cause Modal -->
    <UModal v-model:open="showCauseModal">
      <template #content>
        <div class="w-full rounded-xl bg-white shadow-xl">
          <div class="flex items-center justify-between border-b border-slate-100 px-6 py-5">
            <h3 class="text-base font-semibold text-slate-900">{{ causeEditing ? "Edit Downtime Cause" : "Add Downtime Cause" }}</h3>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showCauseModal = false" />
          </div>
          <div class="space-y-4 px-6 py-5">
            <UFormField label="Name" required>
              <UInput v-model="causeForm.name" placeholder="e.g. Mechanical Failure" class="w-full" />
            </UFormField>
            <UFormField label="Description">
              <UTextarea v-model="causeForm.description" :rows="3" class="w-full" />
            </UFormField>
            <UFormField label="Active">
              <UToggle v-model="causeForm.active" />
            </UFormField>
          </div>
          <UAlert v-if="causeError" color="error" variant="soft" :description="causeError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showCauseModal = false">Cancel</UButton>
            <UButton :loading="savingCause" @click="saveCause">Save</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Downtime Cause Delete Modal -->
    <UModal v-model:open="showDeleteCauseModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Downtime Cause</h3></template>
          <p class="text-sm text-slate-500">Delete <strong>{{ deleteCauseTarget?.name }}</strong>? This cannot be undone.</p>
          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton variant="ghost" @click="deleteCauseTarget = null">Cancel</UButton>
              <UButton color="error" :loading="deletingCause" @click="confirmDeleteCause">Delete</UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
    <!-- Part Category Modal -->
    <UModal v-model:open="showCategoryModal">
      <template #content>
        <div class="w-full rounded-xl bg-white shadow-xl">
          <div class="flex items-center justify-between border-b border-slate-100 px-6 py-5">
            <h3 class="text-base font-semibold text-slate-900">{{ categoryEditing ? "Edit Category" : "Add Category" }}</h3>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showCategoryModal = false" />
          </div>
          <div class="px-6 py-5">
            <UFormField label="Name" required>
              <UInput v-model="categoryForm.name" placeholder="e.g. Bearings" class="w-full" />
            </UFormField>
          </div>
          <UAlert v-if="categoryError" color="error" variant="soft" :description="categoryError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showCategoryModal = false">Cancel</UButton>
            <UButton :loading="savingCategory" @click="saveCategory">Save</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Part Category Delete Modal -->
    <UModal v-model:open="showDeleteCategoryModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Part Category</h3></template>
          <p class="text-sm text-slate-500">Delete category <strong>{{ deleteCategoryTarget?.name }}</strong>? This cannot be undone.</p>
          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton variant="ghost" @click="deleteCategoryTarget = null">Cancel</UButton>
              <UButton color="error" :loading="deletingCategory" @click="confirmDeleteCategory">Delete</UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
    <!-- Inspection Template Modal -->
    <UModal v-model:open="showTemplateModal">
      <template #content>
        <div class="w-full max-w-lg rounded-xl bg-white shadow-xl">
          <div class="flex items-center justify-between border-b border-slate-100 px-6 py-5">
            <h3 class="text-base font-semibold text-slate-900">{{ templateEditing ? "Edit Template" : "Add Inspection Template" }}</h3>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showTemplateModal = false" />
          </div>
          <div class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
            <UFormField label="Name" required class="col-span-2">
              <UInput v-model="templateForm.name" placeholder="e.g. Daily Baler Check" class="w-full" />
            </UFormField>
            <UFormField label="Asset Type" required>
              <USelect v-model="templateForm.asset_type" :items="assetTypeOptions" placeholder="Select type" class="w-full" />
            </UFormField>
            <UFormField label="Frequency" required>
              <USelect v-model="templateForm.frequency" :items="frequencyOptions" class="w-full" />
            </UFormField>
            <UFormField label="Active" class="col-span-2">
              <UToggle v-model="templateForm.active" />
            </UFormField>
            <UFormField label="Notes" class="col-span-2">
              <UTextarea v-model="templateForm.notes" :rows="2" class="w-full" />
            </UFormField>
          </div>
          <UAlert v-if="templateError" color="error" variant="soft" :description="templateError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showTemplateModal = false">Cancel</UButton>
            <UButton :loading="savingTemplate" @click="saveTemplate">{{ templateEditing ? "Save Changes" : "Create Template" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Template Delete Modal -->
    <UModal v-model:open="showDeleteTemplateModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Template</h3></template>
          <p class="text-sm text-slate-500">Delete template <strong>{{ deleteTemplateTarget?.name }}</strong>? This will also remove all its questions. This cannot be undone.</p>
          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton variant="ghost" @click="deleteTemplateTarget = null">Cancel</UButton>
              <UButton color="error" :loading="deletingTemplate" @click="confirmDeleteTemplate">Delete</UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>

    <!-- Template Items Modal -->
    <UModal v-model:open="showItemsModal" :ui="{ content: 'max-w-2xl' }">
      <template #content>
        <div class="w-full max-w-2xl rounded-xl bg-white shadow-xl">
          <div class="flex items-center justify-between border-b border-slate-100 px-6 py-5">
            <div>
              <h3 class="text-base font-semibold text-slate-900">{{ activeTemplate?.name }} — Questions</h3>
              <p class="text-sm text-slate-500">Manage checklist items for this template</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showItemsModal = false" />
          </div>

          <div v-if="!showItemForm" class="p-6 space-y-4">
            <div class="flex justify-end">
              <UButton size="xs" leading-icon="i-heroicons-plus" @click="openCreateItem">Add Question</UButton>
            </div>
            <div v-if="loadingItems" class="py-8 text-center text-sm text-slate-400">Loading…</div>
            <UTable v-else :data="templateItems" :columns="itemColumns">
              <template #is_critical-cell="{ row: { original: row } }">
                <UBadge v-if="row.is_critical" color="error" variant="soft" size="xs">Critical</UBadge>
                <span v-else class="text-slate-400 text-sm">—</span>
              </template>
              <template #category-cell="{ row: { original: row } }">
                <span class="text-slate-500">{{ row.category ?? "—" }}</span>
              </template>
              <template #actions-cell="{ row: { original: row } }">
                <div class="flex items-center gap-1">
                  <UButton variant="ghost" size="xs" icon="i-heroicons-pencil" @click="openEditItem(row)" />
                  <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteItem(row.id!)" />
                </div>
              </template>
            </UTable>
            <p v-if="!loadingItems && !templateItems.length" class="text-sm text-slate-400">No questions yet.</p>
          </div>

          <!-- Inline item form -->
          <div v-else class="p-6 space-y-4">
            <h4 class="font-medium text-slate-800">{{ itemEditing ? "Edit Question" : "New Question" }}</h4>
            <UFormField label="Question" required>
              <UTextarea v-model="itemForm.question" :rows="2" class="w-full" />
            </UFormField>
            <div class="grid grid-cols-2 gap-4">
              <UFormField label="Category">
                <UInput v-model="itemForm.category" placeholder="e.g. Safety, Mechanical" class="w-full" />
              </UFormField>
              <UFormField label="Order">
                <UInput v-model.number="itemForm.order" type="number" class="w-full" />
              </UFormField>
            </div>
            <UFormField label="Critical">
              <UToggle v-model="itemForm.is_critical" />
            </UFormField>
            <UAlert v-if="itemError" color="error" variant="soft" :description="itemError" />
            <div class="flex justify-end gap-3">
              <UButton variant="ghost" color="neutral" @click="showItemForm = false">Cancel</UButton>
              <UButton :loading="savingItem" @click="saveItem">Save Question</UButton>
            </div>
          </div>
        </div>
      </template>
    </UModal>
    <!-- PM Plan Modal -->
    <UModal v-model:open="showPmPlanModal">
      <template #content>
        <div class="w-full max-w-lg rounded-xl bg-white shadow-xl">
          <div class="flex items-center justify-between border-b border-slate-100 px-6 py-5">
            <h3 class="text-base font-semibold text-slate-900">{{ pmPlanEditing ? `Edit Plan: ${pmPlanEditing.pm_id}` : "Add PM Plan" }}</h3>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showPmPlanModal = false" />
          </div>
          <div class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
            <UFormField label="Plan ID" required>
              <UInput v-model="pmPlanForm.pm_id" placeholder="e.g. PM-BAL-001" :disabled="!!pmPlanEditing" class="w-full" />
            </UFormField>
            <UFormField label="Asset Type" required>
              <USelect v-model="pmPlanForm.asset_type" :items="assetTypeOptionsForPm" placeholder="Select type" class="w-full" />
            </UFormField>
            <UFormField label="Frequency" required>
              <USelect v-model="pmPlanForm.frequency" :items="pmFrequencyOptions" class="w-full" />
            </UFormField>
            <UFormField label="Trigger">
              <USelect v-model="pmPlanForm.trigger" :items="pmTriggerOptions" class="w-full" />
            </UFormField>
            <UFormField label="Owner">
              <USelect v-model="pmPlanForm.owner" :items="pmOwnerOptions" class="w-full" />
            </UFormField>
            <UFormField label="Description" class="col-span-2">
              <UTextarea v-model="pmPlanForm.description" :rows="2" class="w-full" />
            </UFormField>
            <UFormField label="Notes" class="col-span-2">
              <UTextarea v-model="pmPlanForm.notes" :rows="2" class="w-full" />
            </UFormField>
          </div>
          <UAlert v-if="pmPlanError" color="error" variant="soft" :description="pmPlanError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showPmPlanModal = false">Cancel</UButton>
            <UButton :loading="savingPmPlan" @click="savePmPlan">{{ pmPlanEditing ? "Save Changes" : "Create Plan" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- PM Plan Delete Modal -->
    <UModal v-model:open="showDeletePmPlanModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete PM Plan</h3></template>
          <p class="text-sm text-slate-500">Delete plan <strong>{{ deletePmPlanTarget?.pm_id }}</strong>? Any asset PMs linked to this plan will lose their plan reference.</p>
          <template #footer>
            <div class="flex justify-end gap-2">
              <UButton variant="ghost" @click="deletePmPlanTarget = null">Cancel</UButton>
              <UButton color="error" :loading="deletingPmPlan" @click="confirmDeletePmPlan">Delete</UButton>
            </div>
          </template>
        </UCard>
      </template>
    </UModal>
  </div>
</template>
