export function useApi() {
  const config = useRuntimeConfig()
  const base = config.public.apiBase
  const { token } = useAuth()

  function authHeaders(): Record<string, string> {
    return token.value ? { Authorization: `Bearer ${token.value}` } : {}
  }

  async function get<T>(path: string): Promise<T> {
    return $fetch<T>(`${base}${path}`, { headers: authHeaders() })
  }

  async function post<T>(path: string, body: unknown): Promise<T> {
    return $fetch<T>(`${base}${path}`, { method: "POST", body, headers: authHeaders() })
  }

  async function put<T>(path: string, body: unknown): Promise<T> {
    return $fetch<T>(`${base}${path}`, { method: "PUT", body, headers: authHeaders() })
  }

  async function del(path: string): Promise<void> {
    return $fetch(`${base}${path}`, { method: "DELETE", headers: authHeaders() })
  }

  return { get, post, put, del }
}
