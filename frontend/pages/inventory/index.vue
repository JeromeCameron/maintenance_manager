<script setup lang="ts">
import type { Part } from "~/types"

const { getParts, removePart, getCategories, getStockLevels } = useInventory()

const { data: parts, refresh } = await useAsyncData("parts", () => getParts())
const { data: categories } = await useAsyncData("part-cats", () => getCategories())
const { data: stockLevels } = await useAsyncData("stock-levels", () => getStockLevels())

const catMap = computed(() => {
  const m: Record<number, string> = {}
  for (const c of categories.value ?? []) {
    if (c.id != null) m[c.id] = c.name
  }
  return m
})

const stockMap = computed(() => {
  const m: Record<string, number> = {}
  for (const s of stockLevels.value ?? []) {
    if (s.part_no) m[s.part_no] = (m[s.part_no] ?? 0) + s.quantity
  }
  return m
})

const columns = [
  { accessorKey: "part_no", header: "Part No" },
  { accessorKey: "part_name", header: "Name" },
  { accessorKey: "manufacturer", header: "Manufacturer" },
  { accessorKey: "category_id", header: "Category" },
  { accessorKey: "unit_of_measure", header: "UOM" },
  { id: "stock", header: "Stock" },
  { accessorKey: "reorder_level", header: "Reorder At" },
  { accessorKey: "is_critical", header: "Critical" },
  { id: "actions", header: "" },
]

const search = ref("")
const filtered = computed(() =>
  (parts.value ?? []).filter((p) => {
    const q = search.value.toLowerCase()
    return !q || p.part_no.toLowerCase().includes(q) || p.part_name.toLowerCase().includes(q)
  })
)

const lowStock = computed(() =>
  (parts.value ?? []).filter((p) => (stockMap.value[p.part_no] ?? 0) <= p.reorder_level)
)

const deleteTarget = ref<Part | null>(null)
const deleting = ref(false)
const showDeleteModal = computed({ get: () => !!deleteTarget.value, set: (v) => { if (!v) deleteTarget.value = null } })

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await removePart(deleteTarget.value.part_no)
    await refresh()
    deleteTarget.value = null
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Inventory</h1>
      <UButton to="/inventory/new" leading-icon="i-heroicons-plus">New Part</UButton>
    </div>

    <UAlert
      v-if="lowStock.length"
      color="warning"
      variant="soft"
      icon="i-heroicons-exclamation-triangle"
      :title="`${lowStock.length} part${lowStock.length > 1 ? 's' : ''} at or below reorder level`"
    />

    <UCard>
      <template #header>
        <UInput
          v-model="search"
          placeholder="Search by part no or name..."
          leading-icon="i-heroicons-magnifying-glass"
          class="max-w-sm"
        />
      </template>

      <UTable :data="filtered" :columns="columns">
        <template #category_id-cell="{ row }">
          {{ catMap[row.category_id] ?? "—" }}
        </template>
        <template #stock-cell="{ row }">
          <span
            :class="(stockMap[row.part_no] ?? 0) <= row.reorder_level
              ? 'font-semibold text-warning-600 dark:text-warning-400'
              : 'font-medium'"
          >
            {{ stockMap[row.part_no] ?? 0 }}
          </span>
        </template>
        <template #is_critical-cell="{ row }">
          <UBadge v-if="row.is_critical" color="error" variant="soft" size="sm">Critical</UBadge>
          <span v-else class="text-gray-400">—</span>
        </template>
        <template #actions-cell="{ row }">
          <div class="flex items-center gap-1">
            <UButton :to="`/inventory/${row.part_no}`" variant="ghost" size="xs" icon="i-heroicons-pencil" />
            <UButton variant="ghost" size="xs" icon="i-heroicons-trash" color="error" @click="deleteTarget = row" />
          </div>
        </template>
      </UTable>
    </UCard>

    <UModal v-model:open="showDeleteModal">
      <template #content>
        <UCard>
          <template #header><h3 class="font-semibold">Delete Part</h3></template>
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Delete part <strong>{{ deleteTarget?.part_no }}</strong>? This cannot be undone.
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
