import type { User } from "~/types"

export function useUsers() {
  const { get, post, put, del } = useApi()

  const getAll = () => get<User[]>("/users")
  const getOne = (id: number) => get<User>(`/users/${id}`)
  const create = (data: User) => post<User>("/users", data)
  const update = (id: number, data: User) => put<User>(`/users/${id}`, data)
  const remove = (id: number) => del(`/users/${id}`)

  return { getAll, getOne, create, update, remove }
}
