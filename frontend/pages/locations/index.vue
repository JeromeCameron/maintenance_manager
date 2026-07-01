<script setup lang="ts">
import type { Location, Asset, AssetModel, AssetCategory } from "~/types"

const { isAdmin } = useAuth()
const { getAll, getOne, create, update, remove } = useLocations()
const { getByLocation } = useAssets()
const { getAll: getAllModels } = useAssetModels()

const { data: locations, refresh } = await useAsyncData("locations", () => getAll())

const columns = [
  { accessorKey: "location_id", header: "ID" },
  { accessorKey: "name", header: "Name" },
  { accessorKey: "parish", header: "Parish" },
  { accessorKey: "typ", header: "Type" },
  { accessorKey: "supervisor", header: "Supervisor" },
  { accessorKey: "contact_no", header: "Contact" },
  { accessorKey: "shift_depot", header: "Shift Depot" },
  { id: "actions", header: "" },
]

const search = ref("")
const filtered = computed(() =>
  (locations.value ?? []).filter((l) => {
    const q = search.value.toLowerCase()
    return !q || l.name.toLowerCase().includes(q) || l.parish.toLowerCase().includes(q) || l.supervisor.toLowerCase().includes(q)
  })
)

const typeOptions = ["depot", "redemption_centre"]

// ── Form modal ───────────────────────────────────────────────
const showModal = ref(false)
const isEditing = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const formError = ref<string | null>(null)
const activeTab = ref("details")

const defaultForm = (): Partial<Location> => ({ typ: "depot", shift_depot: false, shift_length: 8 })
const form = ref<Partial<Location>>(defaultForm())

// ── Profile data ─────────────────────────────────────────────
const profileLoading = ref(false)
const locationAssets = ref<Asset[]>([])
const assetModels = ref<AssetModel[]>([])

const categoryMeta: Record<AssetCategory, { label: string; icon: string; color: string; bg: string; border: string }> = {
  baler:    { label: "Balers",     icon: "i-heroicons-cube-transparent",  color: "text-blue-600",   bg: "bg-blue-50",   border: "border-blue-200" },
  conveyor: { label: "Conveyors",  icon: "i-heroicons-arrows-right-left", color: "text-purple-600", bg: "bg-purple-50", border: "border-purple-200" },
  bobcat:   { label: "Bobcats",    icon: "i-heroicons-truck",             color: "text-amber-600",  bg: "bg-amber-50",  border: "border-amber-200" },
  forklift: { label: "Forklifts",  icon: "i-heroicons-arrow-up-tray",     color: "text-orange-600", bg: "bg-orange-50", border: "border-orange-200" },
  scale:    { label: "Scales",     icon: "i-heroicons-scale",             color: "text-teal-600",   bg: "bg-teal-50",   border: "border-teal-200" },
}

const statusMeta: Record<string, { label: string; color: string; dot: string }> = {
  operational:    { label: "Operational",    color: "text-emerald-700", dot: "bg-emerald-500" },
  maintenance:    { label: "Maintenance",    color: "text-amber-700",   dot: "bg-amber-500" },
  out_of_service: { label: "Out of Service", color: "text-red-700",     dot: "bg-red-500" },
  disposed:       { label: "Disposed",       color: "text-slate-500",   dot: "bg-slate-400" },
}

// Fleet summary stats
const fleetStats = computed(() => {
  const all = locationAssets.value
  return {
    total: all.length,
    operational: all.filter(a => a.status === "operational").length,
    maintenance: all.filter(a => a.status === "maintenance").length,
    out_of_service: all.filter(a => a.status === "out_of_service").length,
    disposed: all.filter(a => a.status === "disposed").length,
  }
})

// Equipment grouped by category
const equipmentByCategory = computed(() => {
  const groups: Record<string, { assets: Asset[]; meta: typeof categoryMeta[AssetCategory] }> = {}
  for (const asset of locationAssets.value) {
    const cat = asset.category as AssetCategory
    if (!groups[cat]) groups[cat] = { assets: [], meta: categoryMeta[cat] }
    groups[cat].assets.push(asset)
  }
  return Object.entries(groups).sort((a, b) => b[1].assets.length - a[1].assets.length)
})

// Baling potential
const balerInfo = computed(() => {
  const balers = locationAssets.value.filter(a => a.category === "baler")
  if (!balers.length) return null

  const shiftHours = form.value.shift_length ?? 8
  const shiftMinutes = shiftHours * 60

  const rows = balers.map(baler => {
    const model = baler.model_no ? assetModels.value.find(m => m.model_no === baler.model_no) : null
    const balesPerShift = model?.bale_time ? Math.floor(shiftMinutes / model.bale_time) : null
    const weightPerShift = balesPerShift != null && model?.bale_weight ? balesPerShift * model.bale_weight : null
    return {
      asset_id: baler.asset_id,
      alias: baler.alias,
      manufacturer: baler.manufacturer,
      model_no: baler.model_no,
      status: baler.status,
      bale_weight: model?.bale_weight ?? null,
      bale_time: model?.bale_time ?? null,
      baler_type: model?.baler_type ?? null,
      balesPerShift,
      weightPerShift,
      isOperational: baler.status === "operational",
    }
  })

  const operational = rows.filter(r => r.isOperational)
  const totalBalesPerShift = operational.reduce((s, r) => s + (r.balesPerShift ?? 0), 0)
  const totalWeightPerShift = operational.reduce((s, r) => s + (r.weightPerShift ?? 0), 0)
  const hasSpecs = rows.some(r => r.bale_time != null)

  return { rows, operational, totalBalesPerShift, totalWeightPerShift, hasSpecs, shiftHours }
})

function fmtWeight(lbs: number): string {
  const tonnes = lbs / 2204.62
  return tonnes >= 1 ? `${tonnes.toFixed(1)} t` : `${lbs.toLocaleString()} lbs`
}

function openCreate() {
  form.value = defaultForm()
  isEditing.value = false
  editId.value = null
  formError.value = null
  activeTab.value = "details"
  locationAssets.value = []
  assetModels.value = []
  showModal.value = true
}

async function openEdit(id: number) {
  form.value = { ...await getOne(id) }
  isEditing.value = true
  editId.value = id
  formError.value = null
  activeTab.value = "details"
  showModal.value = true

  profileLoading.value = true
  try {
    const [assetList, modelList] = await Promise.all([
      getByLocation(id).catch(() => [] as Asset[]),
      getAllModels().catch(() => [] as AssetModel[]),
    ])
    locationAssets.value = assetList
    assetModels.value = modelList
  } finally {
    profileLoading.value = false
  }
}

async function save() {
  saving.value = true
  formError.value = null
  try {
    if (isEditing.value && editId.value) {
      await update(editId.value, form.value as Location)
    } else {
      await create(form.value as Location)
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
const deleteTarget = ref<Location | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value?.location_id) return
  deleting.value = true
  try {
    await remove(deleteTarget.value.location_id)
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
          <UInput v-model="search" placeholder="Search by name, parish or supervisor..." leading-icon="i-heroicons-magnifying-glass" class="max-w-sm" />
          <UButton leading-icon="i-heroicons-plus" @click="openCreate" class="!bg-blue-700 hover:!bg-blue-800">New Location</UButton>
        </div>
      </template>
      <UTable :data="filtered" :columns="columns" :ui="{ th: 'bg-slate-100 text-slate-500 font-semibold', tr: 'odd:bg-white even:bg-slate-50 hover:bg-blue-50 transition-colors' }">
        <template #typ-cell="{ row: { original: row } }">
          <UBadge :color="row.typ === 'depot' ? 'info' : 'neutral'" variant="soft" size="sm">{{ row.typ.replace(/_/g, " ") }}</UBadge>
        </template>
        <template #shift_depot-cell="{ row: { original: row } }">
          <UBadge v-if="row.shift_depot" color="success" variant="soft" size="sm">Yes</UBadge>
          <span v-else class="text-slate-400">—</span>
        </template>
        <template #actions-cell="{ row: { original: row } }">
          <div class="flex items-center gap-1">
            <UButton variant="ghost" size="xs" icon="i-heroicons-eye" @click="openEdit(row.location_id)" />
            <UButton v-if="isAdmin" variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <!-- Create / Edit Modal -->
    <UModal v-model:open="showModal" :ui="{ content: isEditing ? 'max-w-4xl' : 'max-w-2xl' }">
      <template #content>
        <div class="flex max-h-[90vh] w-full flex-col rounded-xl bg-white shadow-xl" :class="isEditing ? 'max-w-4xl' : 'max-w-2xl'">

          <!-- Header -->
          <div class="flex shrink-0 items-start gap-4 border-b border-slate-100 px-6 py-5">
            <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50">
              <UIcon name="i-heroicons-map-pin" class="h-5 w-5 text-blue-600" />
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900">{{ isEditing ? form.name : "New Location" }}</h3>
              <p class="text-sm text-slate-500">{{ isEditing ? `${form.parish} · ${form.typ?.replace(/_/g, " ")}` : "Add a new location" }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showModal = false" />
          </div>

          <!-- Tab bar (edit only) -->
          <div v-if="isEditing" class="flex shrink-0 border-b border-gray-200 px-6">
            <button
              v-for="tab in [{ value: 'details', label: 'Details' }, { value: 'profile', label: 'Location Profile' }]"
              :key="tab.value"
              class="border-b-2 px-5 py-3 text-sm font-medium transition-colors"
              :class="activeTab === tab.value ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
              @click="activeTab = tab.value"
            >
              {{ tab.label }}
            </button>
          </div>

          <!-- Scrollable body -->
          <div class="flex-1 overflow-y-auto">

            <!-- Details tab -->
            <div v-if="!isEditing || activeTab === 'details'" class="grid grid-cols-2 gap-x-5 gap-y-4 px-6 py-5">
              <UFormField label="Name" required>
                <UInput v-model="form.name" placeholder="e.g. Kingston Depot" class="w-full" />
              </UFormField>
              <UFormField label="Type" required>
                <USelect v-model="form.typ" :items="typeOptions" class="w-full" />
              </UFormField>
              <UFormField label="Parish" required>
                <UInput v-model="form.parish" placeholder="e.g. St. Andrew" class="w-full" />
              </UFormField>
              <UFormField label="Supervisor" required>
                <UInput v-model="form.supervisor" class="w-full" />
              </UFormField>
              <UFormField label="Contact No" required>
                <UInput v-model="form.contact_no" type="tel" class="w-full" />
              </UFormField>
              <UFormField label="Shift Length (hrs)">
                <UInput v-model.number="form.shift_length" type="number" class="w-full" />
              </UFormField>
              <UFormField label="Latitude">
                <UInput v-model="form.latitude" placeholder="e.g. 17.9971" class="w-full" />
              </UFormField>
              <UFormField label="Longitude">
                <UInput v-model="form.longitude" placeholder="e.g. -76.7936" class="w-full" />
              </UFormField>
              <UFormField label="Shift Depot" class="col-span-2">
                <UCheckbox v-model="form.shift_depot" label="This is a shift depot" />
              </UFormField>
              <UAlert v-if="formError" color="error" variant="soft" :description="formError" class="col-span-2" />
            </div>

            <!-- Profile tab -->
            <div v-else-if="activeTab === 'profile'" class="px-6 py-5 space-y-6">

              <div v-if="profileLoading" class="flex items-center justify-center py-16 text-sm text-slate-400">
                <UIcon name="i-heroicons-arrow-path" class="mr-2 h-4 w-4 animate-spin" />
                Loading profile…
              </div>

              <template v-else>

                <!-- Fleet summary stat row -->
                <div class="grid grid-cols-4 gap-3">
                  <div class="rounded-xl border border-slate-200 bg-white p-4 text-center shadow-sm">
                    <p class="text-2xl font-bold text-slate-800">{{ fleetStats.total }}</p>
                    <p class="mt-0.5 text-xs font-medium uppercase tracking-wide text-slate-500">Total Equipment</p>
                  </div>
                  <div class="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-center shadow-sm">
                    <p class="text-2xl font-bold text-emerald-700">{{ fleetStats.operational }}</p>
                    <p class="mt-0.5 text-xs font-medium uppercase tracking-wide text-emerald-600">Operational</p>
                  </div>
                  <div class="rounded-xl border border-amber-200 bg-amber-50 p-4 text-center shadow-sm">
                    <p class="text-2xl font-bold text-amber-700">{{ fleetStats.maintenance }}</p>
                    <p class="mt-0.5 text-xs font-medium uppercase tracking-wide text-amber-600">Maintenance</p>
                  </div>
                  <div class="rounded-xl border border-red-200 bg-red-50 p-4 text-center shadow-sm">
                    <p class="text-2xl font-bold text-red-700">{{ fleetStats.out_of_service }}</p>
                    <p class="mt-0.5 text-xs font-medium uppercase tracking-wide text-red-600">Out of Service</p>
                  </div>
                </div>

                <!-- Empty state -->
                <div v-if="fleetStats.total === 0" class="rounded-xl border border-dashed border-slate-300 py-12 text-center">
                  <UIcon name="i-heroicons-building-office-2" class="mx-auto mb-2 h-8 w-8 text-slate-300" />
                  <p class="text-sm text-slate-400">No equipment assigned to this location</p>
                </div>

                <template v-else>

                  <!-- Equipment by category -->
                  <div>
                    <h4 class="mb-3 text-sm font-semibold text-slate-700">Equipment by Type</h4>
                    <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
                      <div
                        v-for="[cat, group] in equipmentByCategory"
                        :key="cat"
                        class="rounded-xl border p-4"
                        :class="[group.meta.bg, group.meta.border]"
                      >
                        <div class="flex items-center gap-2">
                          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-white/70">
                            <UIcon :name="group.meta.icon" class="h-4 w-4" :class="group.meta.color" />
                          </div>
                          <div>
                            <p class="text-lg font-bold text-slate-800">{{ group.assets.length }}</p>
                            <p class="text-xs font-medium text-slate-600">{{ group.meta.label }}</p>
                          </div>
                        </div>
                        <!-- Status breakdown -->
                        <div class="mt-3 flex flex-wrap gap-x-3 gap-y-1">
                          <template v-for="(sm, status) in statusMeta" :key="status">
                            <span
                              v-if="group.assets.filter(a => a.status === status).length"
                              class="flex items-center gap-1 text-xs text-slate-500"
                            >
                              <span class="inline-block h-1.5 w-1.5 rounded-full" :class="sm.dot" />
                              {{ group.assets.filter(a => a.status === status).length }} {{ sm.label }}
                            </span>
                          </template>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Baling Potential (only if balers exist) -->
                  <div v-if="balerInfo">
                    <h4 class="mb-3 text-sm font-semibold text-slate-700">Baling Potential</h4>
                    <div class="overflow-hidden rounded-xl border border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50">

                      <!-- Summary row -->
                      <div v-if="balerInfo.hasSpecs && balerInfo.operational.length" class="grid grid-cols-3 divide-x divide-blue-200 border-b border-blue-200">
                        <div class="px-5 py-4 text-center">
                          <p class="text-2xl font-bold text-blue-700">{{ balerInfo.operational.length }}</p>
                          <p class="mt-0.5 text-xs font-medium uppercase tracking-wide text-blue-500">Active Balers</p>
                        </div>
                        <div class="px-5 py-4 text-center">
                          <p class="text-2xl font-bold text-blue-700">{{ balerInfo.totalBalesPerShift }}</p>
                          <p class="mt-0.5 text-xs font-medium uppercase tracking-wide text-blue-500">Bales / {{ balerInfo.shiftHours }}h shift</p>
                        </div>
                        <div class="px-5 py-4 text-center">
                          <p class="text-2xl font-bold text-blue-700">{{ fmtWeight(balerInfo.totalWeightPerShift) }}</p>
                          <p class="mt-0.5 text-xs font-medium uppercase tracking-wide text-blue-500">Weight / shift</p>
                        </div>
                      </div>
                      <div v-else-if="!balerInfo.hasSpecs" class="px-5 py-3 text-center text-xs text-blue-400">
                        Model specs not configured — baling capacity unavailable
                      </div>
                      <div v-else-if="!balerInfo.operational.length" class="px-5 py-3 text-center text-xs text-amber-600">
                        No operational balers — {{ balerInfo.rows.length }} baler(s) offline
                      </div>

                      <!-- Per-baler breakdown -->
                      <div class="divide-y divide-blue-100">
                        <div v-for="baler in balerInfo.rows" :key="baler.asset_id" class="flex items-center gap-3 px-5 py-3">
                          <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full" :class="baler.isOperational ? 'bg-blue-100' : 'bg-slate-100'">
                            <UIcon name="i-heroicons-cube-transparent" class="h-3.5 w-3.5" :class="baler.isOperational ? 'text-blue-600' : 'text-slate-400'" />
                          </div>
                          <div class="flex-1 min-w-0">
                            <p class="truncate text-sm font-medium text-slate-800">
                              {{ baler.alias ?? baler.asset_id }}
                              <span v-if="baler.baler_type" class="ml-1 text-xs text-slate-400 capitalize">({{ baler.baler_type }})</span>
                            </p>
                            <p class="text-xs text-slate-500">{{ baler.manufacturer }}{{ baler.model_no ? ` · ${baler.model_no}` : "" }}</p>
                          </div>
                          <div class="shrink-0 text-right">
                            <template v-if="baler.balesPerShift != null && baler.isOperational">
                              <p class="text-sm font-semibold text-blue-700">{{ baler.balesPerShift }} bales</p>
                              <p v-if="baler.weightPerShift" class="text-xs text-blue-500">{{ fmtWeight(baler.weightPerShift) }} / shift</p>
                            </template>
                            <template v-else>
                              <UBadge :color="baler.isOperational ? 'neutral' : 'warning'" variant="subtle" size="sm">
                                {{ baler.isOperational ? "No specs" : baler.status.replace(/_/g, " ") }}
                              </UBadge>
                            </template>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Full fleet list -->
                  <div>
                    <h4 class="mb-3 text-sm font-semibold text-slate-700">Fleet</h4>
                    <div class="overflow-hidden rounded-xl border border-slate-200">
                      <table class="w-full text-sm">
                        <thead>
                          <tr class="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                            <th class="px-4 py-2.5">ID</th>
                            <th class="px-4 py-2.5">Name</th>
                            <th class="px-4 py-2.5">Type</th>
                            <th class="px-4 py-2.5">Status</th>
                          </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100">
                          <tr
                            v-for="asset in locationAssets"
                            :key="asset.asset_id"
                            class="hover:bg-slate-50 transition-colors"
                          >
                            <td class="px-4 py-2.5 font-mono text-xs text-slate-600">{{ asset.asset_id }}</td>
                            <td class="px-4 py-2.5">
                              <span class="font-medium text-slate-800">{{ asset.alias ?? asset.manufacturer }}</span>
                              <span v-if="asset.alias" class="ml-1.5 text-xs text-slate-400">{{ asset.manufacturer }}</span>
                            </td>
                            <td class="px-4 py-2.5">
                              <span class="flex items-center gap-1.5">
                                <UIcon :name="categoryMeta[asset.category as AssetCategory]?.icon ?? 'i-heroicons-cube'" class="h-3.5 w-3.5" :class="categoryMeta[asset.category as AssetCategory]?.color" />
                                <span class="capitalize text-slate-600">{{ asset.category }}</span>
                              </span>
                            </td>
                            <td class="px-4 py-2.5">
                              <span class="flex items-center gap-1.5">
                                <span class="h-1.5 w-1.5 rounded-full" :class="statusMeta[asset.status]?.dot ?? 'bg-slate-400'" />
                                <span class="capitalize" :class="statusMeta[asset.status]?.color ?? 'text-slate-600'">
                                  {{ asset.status.replace(/_/g, " ") }}
                                </span>
                              </span>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                </template>
              </template>
            </div>

          </div>

          <!-- Footer -->
          <div class="flex shrink-0 justify-end gap-3 border-t border-slate-100 px-6 py-4">
            <UButton variant="ghost" color="neutral" @click="showModal = false">Cancel</UButton>
            <UButton v-if="!isEditing || activeTab === 'details'" :loading="saving" @click="save">
              {{ isEditing ? "Save Changes" : "Create Location" }}
            </UButton>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Delete Modal -->
    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Location</h3></template>
          <p class="text-sm text-slate-500">Delete location <strong>{{ deleteTarget?.name }}</strong>? This cannot be undone.</p>
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
