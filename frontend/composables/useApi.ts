export function useApi() {
  const config = useRuntimeConfig()
  const base = config.public.apiBase

  async function get<T>(path: string): Promise<T> {
    return $fetch<T>(`${base}${path}`)
  }

  async function post<T>(path: string, body: unknown): Promise<T> {
    return $fetch<T>(`${base}${path}`, { method: "POST", body })
  }

  async function put<T>(path: string, body: unknown): Promise<T> {
    return $fetch<T>(`${base}${path}`, { method: "PUT", body })
  }

  async function del(path: string): Promise<void> {
    return $fetch(`${base}${path}`, { method: "DELETE" })
  }

  return { get, post, put, del }
}
