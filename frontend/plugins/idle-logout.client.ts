const IDLE_MS = 30 * 60 * 1000 // 30 minutes
const WARN_MS = 2 * 60 * 1000  // warn 2 minutes before logout

export default defineNuxtPlugin(() => {
  const { isAuthenticated, logout } = useAuth()

  let idleTimer: ReturnType<typeof setTimeout> | null = null
  let warnTimer: ReturnType<typeof setTimeout> | null = null
  const showWarning = useState("idle_warning", () => false)

  function clearTimers() {
    if (idleTimer) clearTimeout(idleTimer)
    if (warnTimer) clearTimeout(warnTimer)
  }

  function resetTimers() {
    if (!isAuthenticated.value) return
    clearTimers()
    showWarning.value = false

    warnTimer = setTimeout(() => {
      showWarning.value = true
    }, IDLE_MS - WARN_MS)

    idleTimer = setTimeout(() => {
      showWarning.value = false
      logout()
    }, IDLE_MS)
  }

  const EVENTS = ["mousemove", "mousedown", "keydown", "touchstart", "scroll", "click"]

  function onActivity() {
    if (isAuthenticated.value) resetTimers()
  }

  watch(isAuthenticated, (authed) => {
    if (authed) {
      EVENTS.forEach(e => window.addEventListener(e, onActivity, { passive: true }))
      resetTimers()
    } else {
      clearTimers()
      showWarning.value = false
      EVENTS.forEach(e => window.removeEventListener(e, onActivity))
    }
  }, { immediate: true })
})
