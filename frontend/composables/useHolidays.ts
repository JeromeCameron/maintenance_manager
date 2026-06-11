import type { Holiday } from "~/types"

export function useHolidays() {
  const { get, post, put, del } = useApi()

  const getAll = () => get<Holiday[]>("/holidays")
  const create = (data: Holiday) => post<Holiday>("/holidays", data)
  const update = (id: number, data: Holiday) => put<Holiday>(`/holidays/${id}`, data)
  const remove = (id: number) => del(`/holidays/${id}`)

  return { getAll, create, update, remove }
}
