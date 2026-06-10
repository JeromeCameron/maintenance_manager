<script setup lang="ts">
definePageMeta({ layout: false })

const { login, isAuthenticated } = useAuth()

if (isAuthenticated.value) {
  await navigateTo("/")
}

const form = ref({ username: "", password: "" })
const loading = ref(false)
const error = ref<string | null>(null)

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
  <div class="flex min-h-screen items-center justify-center bg-slate-50">
    <div class="w-full max-w-sm">

      <!-- Brand -->
      <div class="mb-8 flex flex-col items-center gap-3">
        <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 shadow-lg shadow-blue-200">
          <UIcon name="i-heroicons-cog-6-tooth" class="h-6 w-6 text-white" />
        </div>
        <div class="text-center">
          <h1 class="text-xl font-bold text-slate-900">Maintenance Manager</h1>
          <p class="text-sm text-slate-500">Sign in to your account</p>
        </div>
      </div>

      <!-- Card -->
      <div class="rounded-2xl bg-white p-8 shadow-sm ring-1 ring-slate-200">
        <form class="space-y-5" @submit.prevent="submit">
          <UFormField label="Username">
            <UInput
              v-model="form.username"
              placeholder="Enter your username"
              leading-icon="i-heroicons-user"
              autocomplete="username"
              class="w-full"
            />
          </UFormField>

          <UFormField label="Password">
            <UInput
              v-model="form.password"
              type="password"
              placeholder="Enter your password"
              leading-icon="i-heroicons-lock-closed"
              autocomplete="current-password"
              class="w-full"
            />
          </UFormField>

          <UAlert
            v-if="error"
            color="error"
            variant="soft"
            :description="error"
          />

          <UButton
            type="submit"
            :loading="loading"
            block
            class="mt-2"
          >
            Sign in
          </UButton>
        </form>
      </div>

      <p class="mt-6 text-center text-xs text-slate-400">
        Maintenance Manager &copy; {{ new Date().getFullYear() }}
      </p>
    </div>
  </div>
</template>
