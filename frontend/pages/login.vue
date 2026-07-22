<script setup lang="ts">
definePageMeta({ layout: false, colorMode: "light" })

const { login, isAuthenticated } = useAuth()

if (isAuthenticated.value) {
  await navigateTo("/")
}

const form = ref({ username: "", password: "" })
const loading = ref(false)
const error = ref<string | null>(null)
const showPassword = ref(false)

async function submit() {
  error.value = null
  loading.value = true
  try {
    await login(form.value.username, form.value.password)
    await navigateTo("/")
  } catch (e: unknown) {
    error.value = (e as { data?: { detail?: string } }).data?.detail ?? "Invalid username or password"
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen bg-white">

    <!-- Left panel — form -->
    <div class="flex w-full flex-col justify-center px-8 py-12 sm:px-12 lg:w-[480px] lg:px-16 xl:px-20">

      <!-- Logo -->
      <div class="mb-10">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 shadow-md shadow-blue-200">
            <UIcon name="i-heroicons-wrench-screwdriver" class="h-5 w-5 text-white" />
          </div>
          <div>
            <p class="text-base font-bold leading-none text-slate-900">Maintenance Manager</p>
            <p class="text-[11px] font-semibold uppercase tracking-widest text-blue-600">CMMS</p>
          </div>
        </div>
      </div>

      <!-- Heading -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-slate-900">Welcome back</h1>
        <p class="mt-1.5 text-sm text-slate-500">Sign in to access your CMMS dashboard</p>
      </div>

      <!-- Form -->
      <form class="space-y-5" @submit.prevent="submit">
        <div>
          <label class="mb-1.5 block text-sm font-medium text-slate-700">Username</label>
          <div class="relative">
            <UIcon name="i-heroicons-user" class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              v-model="form.username"
              type="text"
              placeholder="Enter your username"
              autocomplete="username"
              class="w-full rounded-lg border border-slate-200 bg-white py-2.5 pl-9 pr-4 text-sm text-slate-900 placeholder-slate-400 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />
          </div>
        </div>

        <div>
          <div class="mb-1.5 flex items-center justify-between">
            <label class="text-sm font-medium text-slate-700">Password</label>
          </div>
          <div class="relative">
            <UIcon name="i-heroicons-lock-closed" class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Enter your password"
              autocomplete="current-password"
              class="w-full rounded-lg border border-slate-200 bg-white py-2.5 pl-9 pr-10 text-sm text-slate-900 placeholder-slate-400 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
            />
            <button
              type="button"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              @click="showPassword = !showPassword"
            >
              <UIcon :name="showPassword ? 'i-heroicons-eye-slash' : 'i-heroicons-eye'" class="h-4 w-4" />
            </button>
          </div>
        </div>

        <div v-if="error" class="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-600 ring-1 ring-red-200">
          {{ error }}
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-60"
        >
          <UIcon v-if="loading" name="i-heroicons-arrow-path" class="h-4 w-4 animate-spin" />
          {{ loading ? "Signing in…" : "Sign in" }}
        </button>
      </form>

      <p class="mt-12 text-center text-xs text-slate-400">
        Maintenance Manager &copy; {{ new Date().getFullYear() }}
      </p>
    </div>

    <!-- Right panel — hero -->
    <div class="relative hidden flex-1 lg:flex">
      <!-- Dark gradient overlay -->
      <div class="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-blue-900" />

      <!-- Background pattern -->
      <div class="absolute inset-0 opacity-10"
        style="background-image: radial-gradient(circle at 1px 1px, rgba(255,255,255,0.4) 1px, transparent 0); background-size: 32px 32px;" />

      <!-- Content -->
      <div class="relative flex flex-1 flex-col justify-between p-14">

        <!-- Main text -->
        <div class="mt-16">
          <h2 class="text-5xl font-bold leading-tight text-white">
            Smarter maintenance.<br />Stronger operations.
          </h2>
          <p class="mt-5 max-w-md text-base leading-relaxed text-slate-300">
            Streamline work orders, track assets, and optimize maintenance —
            all in one place.
          </p>
        </div>

        <!-- Feature icons -->
        <div class="grid grid-cols-4 gap-4">
          <div v-for="f in [
            { icon: 'i-heroicons-clipboard-document-list', label: 'Work Order Management' },
            { icon: 'i-heroicons-building-office-2',       label: 'Asset Management' },
            { icon: 'i-heroicons-calendar-days',           label: 'Preventive Maintenance' },
            { icon: 'i-heroicons-chart-bar',               label: 'Reports & Analytics' },
          ]" :key="f.label" class="flex flex-col items-center gap-2 text-center">
            <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-white/10 backdrop-blur-sm ring-1 ring-white/20">
              <UIcon :name="f.icon" class="h-6 w-6 text-blue-300" />
            </div>
            <span class="text-xs font-medium leading-tight text-slate-300">{{ f.label }}</span>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>
