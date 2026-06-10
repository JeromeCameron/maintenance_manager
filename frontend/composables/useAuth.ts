interface AuthUser {
  user_id: number
  username: string
  role: "admin" | "user" | "moderator"
  firstname: string
  lastname: string
}

export const useAuth = () => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase

  const token = useCookie<string | null>("auth_token", {
    maxAge: 60 * 60 * 8, // 8 hours
    sameSite: "strict",
  })

  const user = useState<AuthUser | null>("auth_user", () => null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === "admin")
  const canWrite = computed(() => user.value?.role !== "moderator")
  const isModerator = computed(() => user.value?.role === "moderator")

  async function login(username: string, password: string) {
    const form = new URLSearchParams()
    form.append("username", username)
    form.append("password", password)

    const res = await $fetch<AuthUser & { access_token: string }>(
      `${apiBase}/auth/login`,
      {
        method: "POST",
        body: form.toString(),
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      }
    )

    token.value = res.access_token
    user.value = {
      user_id: res.user_id,
      username: res.username,
      role: res.role,
      firstname: res.firstname,
      lastname: res.lastname,
    }
  }

  function logout() {
    token.value = null
    user.value = null
    navigateTo("/login")
  }

  // Restore user state from token on app load
  async function restoreSession() {
    if (!token.value || user.value) return
    try {
      const me = await $fetch<AuthUser>(`${apiBase}/users/me`, {
        headers: { Authorization: `Bearer ${token.value}` },
      })
      user.value = {
        user_id: me.user_id ?? (me as any).id,
        username: me.username,
        role: me.role,
        firstname: me.firstname,
        lastname: me.lastname,
      }
    } catch {
      token.value = null
    }
  }

  return { token, user, isAuthenticated, isAdmin, canWrite, isModerator, login, logout, restoreSession }
}
