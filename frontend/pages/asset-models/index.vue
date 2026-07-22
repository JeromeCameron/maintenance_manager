<script setup lang="ts">
import type { AssetModel } from "~/types"

const { getAll, getOne, create, update, remove } = useAssetModels()

const { data: models, refresh } = await useAsyncData("asset-models", () => getAll())

const categoryOptions = ["baler", "conveyor", "bobcat", "forklift", "scale"]
const balerTypeOptions = ["vertical", "horizontal"]
const balerSizeOptions = ["small", "medium", "large"]

const isBaler = computed(() => form.value.category === "baler")


const columns = [
  { accessorKey: "model_no", header: "Model No." },
  { accessorKey: "manufacturer", header: "Manufacturer" },
  { accessorKey: "category", header: "Category" },
  { accessorKey: "description", header: "Description" },
  { id: "actions", header: "" },
]

const search = ref("")
const filtered = computed(() =>
  (models.value ?? []).filter((m) => {
    const q = search.value.toLowerCase()
    return !q || m.model_no.toLowerCase().includes(q) || m.manufacturer.toLowerCase().includes(q)
  })
)

// ── Form modal ───────────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const editId = ref<string | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)

const defaultForm = (): Partial<AssetModel> => ({})
const form = ref<Partial<AssetModel>>(defaultForm())

function openCreate() {
  form.value = defaultForm()
  isEditing.value = false
  editId.value = null
  formError.value = null
  showModal.value = true
}

async function openEdit(modelNo: string) {
  form.value = { ...await getOne(modelNo) }
  isEditing.value = true
  editId.value = modelNo
  formError.value = null
  showModal.value = true
}

async function save() {
  saving.value = true
  formError.value = null
  try {
    if (isEditing.value && editId.value) {
      await update(editId.value, form.value as AssetModel)
    } else {
      await create(form.value as AssetModel)
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
const deleteTarget = ref<AssetModel | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({
  get: () => !!deleteTarget.value,
  set: (v) => { if (!v) deleteTarget.value = null },
})

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.model_no)
    await refresh()
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <UCard>
      <template #header>
        <div class="flex items-center justify-between gap-3">
          <UInput v-model="search" placeholder="Search by model no. or manufacturer..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
          <UButton leading-icon="i-heroicons-plus" @click="openCreate" class="!bg-blue-700 hover:!bg-blue-800">New Model</UButton>
        </div>
      </template>
      <UTable :data="filtered" :columns="columns">
        <template #category-cell="{ row: { original: row } }">
          <span class="capitalize">{{ row.category ?? "—" }}</span>
        </template>
        <template #description-cell="{ row: { original: row } }">
          <span class="text-slate-500 dark:text-slate-400">{{ row.description ?? "—" }}</span>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-eye" @click="openEdit(row.model_no)" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Create / Edit Modal -->
    <UModal v-model:open="showModal">
      <template #content>
        <div class="w-full max-w-2xl rounded-xl bg-white dark:bg-slate-900 shadow-xl">
          <div class="flex items-start gap-4 border-b border-slate-100 dark:border-slate-800 px-6 py-5">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 dark:bg-blue-500/10">
              <UIcon name="i-heroicons-cube" class="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">{{ isEditing ? `Edit Model: ${editId}` : "New Asset Model" }}</h3>
              <p class="text-sm text-slate-500 dark:text-slate-400">{{ isEditing ? "Update model details" : "Register a new asset model" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>
          <div class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
            <UFormField label="Model No." required>
              <UInput v-model="form.model_no" placeholder="e.g. HSM-500" :disabled="isEditing" class="w-full" />
            </UFormField>
            <UFormField label="Manufacturer" required>
              <UInput v-model="form.manufacturer" placeholder="e.g. HSM" class="w-full" />
            </UFormField>
            <UFormField label="Category">
              <USelect v-model="form.category" :items="categoryOptions" placeholder="Select category" class="w-full" />
            </UFormField>
            <UFormField label="Description" class="col-span-2">
              <UTextarea v-model="form.description" :rows="3" class="w-full" />
            </UFormField>
            <div v-if="isBaler" class="col-span-2 border-t border-slate-100 dark:border-slate-800 pt-4">
              <p class="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">Baler Specifications</p>
              <div class="grid grid-cols-2 gap-x-5 gap-y-4">
                <UFormField label="Baler Type">
                  <USelect v-model="form.baler_type" :items="balerTypeOptions" placeholder="Select type" class="w-full" />
                </UFormField>
                <UFormField label="Baler Size">
                  <USelect v-model="form.baler_size" :items="balerSizeOptions" placeholder="Select size" class="w-full" />
                </UFormField>
                <UFormField label="Bale Weight (kg)">
                  <UInput v-model.number="form.bale_weight" type="number" class="w-full" />
                </UFormField>
                <UFormField label="Bale Time (min)">
                  <UInput v-model.number="form.bale_time" type="number" class="w-full" />
                </UFormField>
                <UFormField label="Ram Force (kN)">
                  <UInput v-model.number="form.ram_force" type="number" class="w-full" />
                </UFormField>
                <UFormField label="Bale Size">
                  <UInput v-model="form.bale_size" placeholder="e.g. 1200x800x700mm" class="w-full" />
                </UFormField>
              </div>
            </div>
          </div>
          <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="mx-6 mb-4" />
          <div class="flex justify-end gap-3 border-t border-slate-100 dark:border-slate-800 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
            <UButton :loading="saving" @click="save">{{ isEditing ? "Save Changes" : "Create Model" }}</UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Asset Model</h3></template>
          <p class="text-sm text-slate-500 dark:text-slate-400">Delete model <strong>{{ deleteTarget?.model_no }}</strong>? This cannot be undone.</p>
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
