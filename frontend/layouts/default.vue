<script setup lang="ts">
const route = useRoute()
const { user, logout } = useAuth()

const navGroups = [
  {
    label: "Operations",
    items: [
      { label: "Dashboard", icon: "i-heroicons-squares-2x2", to: "/" },
      { label: "Assets", icon: "i-heroicons-wrench-screwdriver", to: "/assets" },
      { label: "Work Orders", icon: "i-heroicons-clipboard-document-list", to: "/work-orders" },
      { label: "Downtime", icon: "i-heroicons-exclamation-triangle", to: "/downtime" },
    ],
  },
  {
    label: "Maintenance",
    items: [
      { label: "PM Schedule", icon: "i-heroicons-calendar-days", to: "/maintenance" },
      { label: "Inspections", icon: "i-heroicons-magnifying-glass", to: "/inspections" },
    ],
  },
  {
    label: "Resources",
    items: [
      { label: "Inventory", icon: "i-heroicons-archive-box", to: "/inventory" },
      { label: "Finance", icon: "i-heroicons-banknotes", to: "/finance" },
    ],
  },
  {
    label: "Admin",
    items: [
      { label: "Locations", icon: "i-heroicons-map-pin", to: "/locations" },
      { label: "Suppliers", icon: "i-heroicons-building-storefront", to: "/suppliers" },
      { label: "Users", icon: "i-heroicons-users", to: "/users" },
    ],
  },
]

const isActive = (to: string) =>
  to === "/" ? route.path === "/" : route.path.startsWith(to)
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-white">

    <!-- Sidebar -->
    <aside class="flex w-60 shrink-0 flex-col bg-slate-900">

      <!-- Brand -->
      <div class="flex h-16 shrink-0 items-center gap-3 border-b border-slate-800 px-4">
        <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600">
          <UIcon name="i-heroicons-cog-6-tooth" class="h-4 w-4 text-white" />
        </div>
        <div class="leading-tight">
          <p class="text-sm font-bold text-white">Maintenance</p>
          <p class="text-[11px] text-slate-400">Manager</p>
        </div>
      </div>

      <!-- Nav groups -->
      <nav class="flex-1 space-y-6 overflow-y-auto px-3 py-5">
        <div v-for="group in navGroups" :key="group.label">
          <p class="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
            {{ group.label }}
          </p>
          <div class="space-y-0.5">
            <NuxtLink
              v-for="item in group.items"
              :key="item.to"
              :to="item.to"
              class="group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-150"
              :class="isActive(item.to)
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:bg-slate-800 hover:text-white'"
            >
              <UIcon
                :name="item.icon"
                class="h-4 w-4 shrink-0"
                :class="isActive(item.to) ? 'text-blue-100' : 'text-slate-500 group-hover:text-slate-300'"
              />
              {{ item.label }}
            </NuxtLink>
          </div>
        </div>
      </nav>

      <!-- User / logout -->
      <div class="shrink-0 border-t border-slate-800 px-3 py-3">
        <div class="flex items-center gap-3 rounded-lg px-3 py-2">
          <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-600">
            <span class="text-[10px] font-bold text-white">
              {{ user ? user.firstname[0] + user.lastname[0] : "?" }}
            </span>
          </div>
          <div class="min-w-0 flex-1">
            <p class="truncate text-xs font-medium text-slate-200">{{ user?.firstname }} {{ user?.lastname }}</p>
            <p class="text-[11px] capitalize text-slate-500">{{ user?.role }}</p>
          </div>
          <UButton
            variant="ghost"
            size="xs"
            icon="i-heroicons-arrow-right-on-rectangle"
            color="neutral"
            class="text-slate-500 hover:text-white"
            @click="logout"
          />
        </div>
      </div>
    </aside>

    <!-- Main area -->
    <div class="flex min-w-0 flex-1 flex-col overflow-hidden">

      <!-- Top bar -->
      <header class="flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6">
        <p class="text-sm font-semibold text-slate-700 capitalize">
          {{ route.path === '/' ? 'Dashboard' : route.path.split('/')[1].replace(/-/g, ' ') }}
        </p>
        <div class="flex items-center gap-2">
          <UButton variant="ghost" size="sm" icon="i-heroicons-bell" color="neutral" />
          <div class="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600">
            <span class="text-xs font-bold text-white">
              {{ user ? user.firstname[0] + user.lastname[0] : '?' }}
            </span>
          </div>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 overflow-y-auto p-6">
        <slot />
      </main>
    </div>
  </div>
</template>
