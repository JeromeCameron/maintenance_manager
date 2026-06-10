export default defineNuxtRouteMiddleware(async (to) => {
  if (to.path === "/login") return

  const { isAuthenticated, restoreSession } = useAuth()

  await restoreSession()

  if (!isAuthenticated.value) {
    return navigateTo("/login")
  }
})
