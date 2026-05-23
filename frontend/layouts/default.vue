<script setup lang="ts">
const route = useRoute()

const nav = [
  { label: "Dashboard", icon: "i-heroicons-squares-2x2", to: "/" },
  { label: "Assets", icon: "i-heroicons-wrench-screwdriver", to: "/assets" },
  { label: "Work Orders", icon: "i-heroicons-clipboard-document-list", to: "/work-orders" },
  { label: "Maintenance", icon: "i-heroicons-calendar-days", to: "/maintenance" },
  { label: "Inspections", icon: "i-heroicons-magnifying-glass", to: "/inspections" },
  { label: "Inventory", icon: "i-heroicons-archive-box", to: "/inventory" },
  { label: "Downtime", icon: "i-heroicons-exclamation-triangle", to: "/downtime" },
  { label: "Finance", icon: "i-heroicons-banknotes", to: "/finance" },
  { label: "Locations", icon: "i-heroicons-map-pin", to: "/locations" },
  { label: "Suppliers", icon: "i-heroicons-building-storefront", to: "/suppliers" },
  { label: "Users", icon: "i-heroicons-users", to: "/users" },
]
</script>

<template>
  <div class="flex h-screen bg-gray-50 dark:bg-gray-950">
    <!-- Sidebar -->
    <aside class="flex w-60 flex-col border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
      <div class="flex h-16 items-center gap-2 border-b border-gray-200 px-4 dark:border-gray-800">
        <UIcon name="i-heroicons-cog-6-tooth" class="h-7 w-7 text-primary-500" />
        <span class="text-sm font-bold tracking-wide text-gray-900 dark:text-white">Maintenance Manager</span>
      </div>

      <nav class="flex-1 space-y-0.5 overflow-y-auto p-2">
        <NuxtLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors"
          :class="route.path === item.to
            ? 'bg-primary-50 text-primary-600 dark:bg-primary-950 dark:text-primary-400'
            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-white'"
        >
          <UIcon :name="item.icon" class="h-5 w-5 flex-shrink-0" />
          {{ item.label }}
        </NuxtLink>
      </nav>
    </aside>

    <!-- Main content -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <main class="flex-1 overflow-y-auto p-6">
        <slot />
      </main>
    </div>
  </div>
</template>
