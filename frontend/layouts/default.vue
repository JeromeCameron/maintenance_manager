<script setup lang="ts">
const route = useRoute()
const { user, logout } = useAuth()
const { get } = useApi()
const { changePassword } = useUsers()
const showIdleWarning = useState("idle_warning", () => false)

// ── Task due-soon reminders (bell) ──────────────────────────────
const { dueSoon: dueSoonTasks, isOverdue: isTaskOverdue, refresh: refreshReminders } = useTaskReminders()
const showReminders = ref(false)

watch(showReminders, (open) => { if (open) refreshReminders() })

const REMINDERS_POLL_MS = 5 * 60 * 1000 // periodic fallback between task edits/dropdown opens
let remindersPollHandle: ReturnType<typeof setInterval> | undefined
onMounted(() => { remindersPollHandle = setInterval(refreshReminders, REMINDERS_POLL_MS) })
onUnmounted(() => clearInterval(remindersPollHandle))

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
function formatDueDate(value: string | null | undefined): string {
  if (!value) return "—"
  const [year, month, day] = value.slice(0, 10).split("-").map(Number)
  if (!year || !month || !day) return "—"
  return `${String(day).padStart(2, "0")}-${MONTHS[month - 1]}-${String(year).slice(-2)}`
}

function goToTasks() {
  showReminders.value = false
  navigateTo("/tasks")
}

// ── Dark mode toggle ────────────────────────────────────────────
const colorMode = useColorMode()
const isDark = computed({
  get: () => colorMode.value === "dark",
  set: (v: boolean) => { colorMode.preference = v ? "dark" : "light" },
})

// ── Profile modal ─────────────────────────────────────────────
const showProfileModal = ref(false)
const profileTab = ref("profile")
const profileTabs = [
  { value: "profile", slot: "profile", label: "Profile", icon: "i-heroicons-user" },
  { value: "password", slot: "password", label: "Change Password", icon: "i-heroicons-key" },
]

interface ProfileData { id: number; username: string; firstname: string; lastname: string; email: string; role: string; active: boolean }
const profileData = ref<ProfileData | null>(null)

async function openProfile() {
  profileTab.value = "profile"
  passwordForm.value = { current: "", new: "", confirm: "" }
  passwordError.value = null
  profileData.value = await get<ProfileData>("/users/me")
  showProfileModal.value = true
}

// ── Change password ───────────────────────────────────────────
const passwordForm = ref({ current: "", new: "", confirm: "" })
const passwordError = ref<string | null>(null)
const passwordSaving = ref(false)

async function submitChangePassword() {
  passwordError.value = null
  if (passwordForm.value.new !== passwordForm.value.confirm) {
    passwordError.value = "New passwords do not match"
    return
  }
  if (!passwordForm.value.new) {
    passwordError.value = "New password cannot be empty"
    return
  }
  passwordSaving.value = true
  try {
    await changePassword(passwordForm.value.current, passwordForm.value.new)
    showProfileModal.value = false
  } catch (e: unknown) {
    passwordError.value = (e as { data?: { detail?: string }; message?: string }).data?.detail ?? (e as { message?: string }).message ?? "Failed to change password"
  } finally {
    passwordSaving.value = false
  }
}

const navGroups = [
  {
    label: "Operations",
    items: [
      { label: "Dashboard", icon: "i-heroicons-squares-2x2", to: "/" },
      { label: "Assets", icon: "i-heroicons-cube", to: "/assets" },
      { label: "Work Orders", icon: "i-heroicons-clipboard-document-list", to: "/work-orders" },
      { label: "Tasks", icon: "i-heroicons-check-circle", to: "/tasks" },
      { label: "Issues", icon: "i-heroicons-flag", to: "/issues" },
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
      { label: "Parts Inventory", icon: "i-heroicons-archive-box", to: "/inventory" },
      { label: "Finance", icon: "i-heroicons-banknotes", to: "/finance" },
      { label: "Reports", icon: "i-heroicons-document-chart-bar", to: "/reports" },
    ],
  },
  {
    label: "Admin",
    items: [
      { label: "Locations", icon: "i-heroicons-map-pin", to: "/locations" },
      { label: "Suppliers", icon: "i-heroicons-building-storefront", to: "/suppliers" },
      { label: "Users", icon: "i-heroicons-users", to: "/users" },
      { label: "Settings", icon: "i-heroicons-cog-6-tooth", to: "/settings" },
    ],
  },
]

const isActive = (to: string) =>
  to === "/" ? route.path === "/" : route.path.startsWith(to)

const pageMap: Record<string, { title: string; caption: string }> = {
  "/assets":      { title: "Assets",      caption: "Manage and monitor your equipment fleet." },
  "/work-orders": { title: "Work Orders", caption: "Track and manage maintenance work orders." },
  "/tasks":       { title: "Tasks",       caption: "Track and manage assigned tasks." },
  "/issues":      { title: "Issues",      caption: "Log and resolve reported equipment issues." },
  "/downtime":    { title: "Downtime",    caption: "Record and analyse equipment downtime events." },
  "/maintenance": { title: "PM Schedule", caption: "Plan and track preventative maintenance." },
  "/inspections": { title: "Inspections", caption: "Conduct and review equipment inspections." },
  "/inventory":   { title: "Parts Inventory", caption: "Manage parts, stock levels and transactions." },
  "/finance":     { title: "Finance",     caption: "Purchase orders, invoices and budget tracking." },
  "/reports":     { title: "Reports",     caption: "Generate and download operational reports." },
  "/locations":   { title: "Locations",   caption: "Manage depots and redemption centres." },
  "/suppliers":   { title: "Suppliers",   caption: "Manage supplier contacts and details." },
  "/users":       { title: "Users",       caption: "Manage user accounts and permissions." },
  "/settings":    { title: "Settings",    caption: "Configure holidays, models and system settings." },
}

const pageInfo = computed(() => {
  if (route.path === "/") return {
    title: `Welcome back, ${user.value?.firstname ?? "there"}.`,
    caption: "Here's a quick snapshot of what's happening.",
  }
  const key = "/" + route.path.split("/")[1]
  return pageMap[key] ?? { title: key.replace("/", "").replace(/-/g, " "), caption: "" }
})
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-white dark:bg-slate-950">

    <!-- Sidebar -->
    <aside class="flex w-60 shrink-0 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">

      <!-- Brand -->
      <div class="flex h-16 shrink-0 items-center gap-3 border-b border-slate-200 px-4 dark:border-slate-800">
        <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-600">
          <UIcon name="i-heroicons-cog-6-tooth" class="h-4 w-4 text-white" />
        </div>
        <div class="leading-tight">
          <p class="text-sm font-bold text-slate-900 dark:text-white">Maintenance</p>
          <p class="text-[11px] text-slate-500 dark:text-slate-400">Manager</p>
        </div>
      </div>

      <!-- Nav groups -->
      <nav class="flex-1 overflow-y-auto space-y-3 px-3 py-3 [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-slate-300 dark:[&::-webkit-scrollbar-thumb]:bg-slate-700 [&::-webkit-scrollbar-track]:bg-transparent">
        <div v-for="group in navGroups" :key="group.label">
          <p class="mb-1 px-3 text-[10px] font-semibold uppercase tracking-widest text-slate-400 dark:text-slate-500">
            {{ group.label }}
          </p>
          <div class="space-y-0.5">
            <NuxtLink
              v-for="item in group.items"
              :key="item.to"
              :to="item.to"
              class="group flex items-center gap-3 rounded-lg px-3 py-1.5 text-sm font-medium transition-all duration-150"
              :class="isActive(item.to)
                ? 'bg-blue-600 text-white'
                : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white'"
            >
              <UIcon
                :name="item.icon"
                class="h-4 w-4 shrink-0"
                :class="isActive(item.to) ? 'text-blue-100' : 'text-slate-400 group-hover:text-slate-600 dark:text-slate-500 dark:group-hover:text-slate-300'"
              />
              {{ item.label }}
            </NuxtLink>
          </div>
        </div>
      </nav>

      <!-- User / logout -->
      <div class="shrink-0 border-t border-slate-200 px-3 py-3 dark:border-slate-800">
        <div class="flex items-center gap-3 rounded-lg px-3 py-2">
          <div class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-600">
            <span class="text-[10px] font-bold text-white">
              {{ user ? user.firstname[0] + user.lastname[0] : "?" }}
            </span>
          </div>
          <div class="min-w-0 flex-1">
            <p class="truncate text-xs font-medium text-slate-700 dark:text-slate-200">{{ user?.firstname }} {{ user?.lastname }}</p>
            <p class="text-[11px] capitalize text-slate-500">{{ user?.role }}</p>
          </div>
          <UButton
            variant="ghost"
            size="xs"
            icon="i-heroicons-arrow-right-on-rectangle"
            color="neutral"
            class="text-slate-500 hover:text-slate-900 dark:hover:text-white"
            @click="logout"
          />
        </div>
      </div>
    </aside>

    <!-- Profile Modal -->
    <UModal v-model:open="showProfileModal">
      <template #content>
        <div class="w-full rounded-xl bg-white shadow-xl dark:bg-slate-900">
          <!-- Header -->
          <div class="flex items-center gap-4 border-b border-slate-100 px-6 py-5 dark:border-slate-800">
            <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-blue-600">
              <span class="text-sm font-bold text-white">
                {{ user ? user.firstname[0] + user.lastname[0] : "?" }}
              </span>
            </div>
            <div class="flex-1">
              <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">{{ user?.firstname }} {{ user?.lastname }}</h3>
              <p class="text-sm capitalize text-slate-500 dark:text-slate-400">{{ user?.role }}</p>
            </div>
            <UButton variant="ghost" size="xs" icon="i-heroicons-x-mark" color="neutral" @click="showProfileModal = false" />
          </div>

          <!-- Tabs -->
          <div class="px-6 pt-4">
            <UTabs v-model="profileTab" :items="profileTabs">
              <template #leading="{ item }">
                <UIcon :name="item.icon" class="h-4 w-4" />
              </template>

              <template #profile>
                <div class="mt-4 space-y-3 pb-6">
                  <div class="grid grid-cols-2 gap-3">
                    <div class="rounded-lg bg-slate-50 px-4 py-3 dark:bg-slate-800">
                      <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">First Name</p>
                      <p class="mt-0.5 text-sm font-medium text-slate-900 dark:text-slate-100">{{ profileData?.firstname }}</p>
                    </div>
                    <div class="rounded-lg bg-slate-50 px-4 py-3 dark:bg-slate-800">
                      <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">Last Name</p>
                      <p class="mt-0.5 text-sm font-medium text-slate-900 dark:text-slate-100">{{ profileData?.lastname }}</p>
                    </div>
                    <div class="rounded-lg bg-slate-50 px-4 py-3 dark:bg-slate-800">
                      <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">Username</p>
                      <p class="mt-0.5 text-sm font-medium text-slate-900 dark:text-slate-100">{{ profileData?.username }}</p>
                    </div>
                    <div class="rounded-lg bg-slate-50 px-4 py-3 dark:bg-slate-800">
                      <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">Role</p>
                      <p class="mt-0.5 text-sm font-medium capitalize text-slate-900 dark:text-slate-100">{{ profileData?.role }}</p>
                    </div>
                    <div class="col-span-2 rounded-lg bg-slate-50 px-4 py-3 dark:bg-slate-800">
                      <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">Email</p>
                      <p class="mt-0.5 text-sm font-medium text-slate-900 dark:text-slate-100">{{ profileData?.email }}</p>
                    </div>
                  </div>
                </div>
              </template>

              <template #password>
                <div class="mt-4 space-y-4 pb-2">
                  <UFormField label="Current Password" required>
                    <UInput v-model="passwordForm.current" type="password" autocomplete="current-password" class="w-full" />
                  </UFormField>
                  <UFormField label="New Password" required>
                    <UInput v-model="passwordForm.new" type="password" autocomplete="new-password" class="w-full" />
                  </UFormField>
                  <UFormField label="Confirm New Password" required>
                    <UInput v-model="passwordForm.confirm" type="password" autocomplete="new-password" class="w-full" />
                  </UFormField>
                  <UAlert v-if="passwordError" color="error" variant="soft" :description="passwordError" />
                  <div class="flex justify-end pt-1 pb-4">
                    <UButton :loading="passwordSaving" @click="submitChangePassword">Change Password</UButton>
                  </div>
                </div>
              </template>
            </UTabs>
          </div>
        </div>
      </template>
    </UModal>

    <!-- Main area -->
    <div class="flex min-w-0 flex-1 flex-col overflow-hidden">

      <!-- Top bar -->
      <header class="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6 dark:border-slate-800 dark:bg-slate-900">
        <div>
          <p class="text-base font-bold text-slate-900 dark:text-slate-100">{{ pageInfo.title }}</p>
          <p v-if="pageInfo.caption" class="text-xs text-slate-400 dark:text-slate-500">{{ pageInfo.caption }}</p>
        </div>
        <div class="flex items-center gap-2">
          <UButton
            variant="ghost"
            size="sm"
            :icon="isDark ? 'i-heroicons-sun' : 'i-heroicons-moon'"
            color="neutral"
            :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
            @click="isDark = !isDark"
          />
          <UPopover v-model:open="showReminders">
            <button
              type="button"
              class="relative flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
              title="Task reminders"
            >
              <UIcon name="i-heroicons-bell" class="h-4 w-4" />
              <span
                v-if="dueSoonTasks.length"
                class="absolute -top-0.5 -right-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white"
              >{{ dueSoonTasks.length }}</span>
            </button>

            <template #content>
              <div class="w-80 rounded-xl bg-white shadow-xl ring-1 ring-gray-200 dark:bg-slate-900 dark:ring-slate-700">
                <div class="flex items-center justify-between border-b border-gray-100 px-4 py-3 dark:border-slate-800">
                  <p class="text-sm font-semibold text-slate-900 dark:text-slate-100">Task Reminders</p>
                  <span class="text-xs text-slate-400 dark:text-slate-500">Due soon or overdue</span>
                </div>
                <div class="max-h-80 overflow-y-auto">
                  <div v-if="dueSoonTasks.length === 0" class="px-4 py-8 text-center text-sm text-gray-400 dark:text-slate-500">
                    No tasks due soon.
                  </div>
                  <button
                    v-for="task in dueSoonTasks"
                    :key="task.id"
                    type="button"
                    class="flex w-full items-start gap-3 border-b border-gray-50 px-4 py-3 text-left transition-colors last:border-b-0 hover:bg-blue-50/40 dark:border-slate-800 dark:hover:bg-blue-500/10"
                    @click="goToTasks"
                  >
                    <span class="mt-1 h-2 w-2 shrink-0 rounded-full" :class="isTaskOverdue(task) ? 'bg-red-500' : 'bg-amber-400'" />
                    <span class="min-w-0 flex-1">
                      <span class="block truncate text-sm font-medium text-slate-800 dark:text-slate-100">{{ task.title }}</span>
                      <span class="mt-0.5 flex items-center gap-1 text-xs" :class="isTaskOverdue(task) ? 'text-red-500' : 'text-amber-600 dark:text-amber-400'">
                        <UIcon name="i-heroicons-clock" class="h-3 w-3" />
                        {{ isTaskOverdue(task) ? 'Overdue' : 'Due' }} {{ formatDueDate(task.due_date) }}
                      </span>
                    </span>
                  </button>
                </div>
                <div class="border-t border-gray-100 px-4 py-2.5 dark:border-slate-800">
                  <button type="button" class="text-xs font-medium text-primary-600 hover:underline" @click="goToTasks">
                    View all tasks
                  </button>
                </div>
              </div>
            </template>
          </UPopover>
          <button
            class="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 hover:bg-blue-700 transition-colors cursor-pointer"
            title="View profile"
            @click="openProfile"
          >
            <span class="text-xs font-bold text-white">
              {{ user ? user.firstname[0] + user.lastname[0] : '?' }}
            </span>
          </button>
        </div>
      </header>

      <!-- Idle warning banner -->
      <Transition enter-from-class="opacity-0 -translate-y-2" enter-active-class="transition duration-200" leave-to-class="opacity-0 -translate-y-2" leave-active-class="transition duration-200">
        <div v-if="showIdleWarning" class="flex items-center justify-between gap-4 bg-amber-500 px-6 py-2.5 text-sm font-medium text-white">
          <div class="flex items-center gap-2">
            <UIcon name="i-heroicons-clock" class="h-4 w-4 shrink-0" />
            <span>You've been inactive for a while. You'll be logged out in 2 minutes.</span>
          </div>
          <UButton size="xs" color="neutral" variant="solid" class="shrink-0 !bg-white !text-amber-700 hover:!bg-amber-50" @click="showIdleWarning = false">
            Stay logged in
          </UButton>
        </div>
      </Transition>

      <!-- Page content -->
      <main class="flex flex-col flex-1 overflow-y-auto bg-slate-50 p-6 dark:bg-slate-950">
        <slot />
      </main>
    </div>
  </div>
</template>
