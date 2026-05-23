import type { Location } from "~/types"

export function useLocations() {
  const { get, post, put, del } = useApi()

  const getAll = () => get<Location[]>("/depots")
  const getOne = (id: number) => get<Location>(`/depots/${id}`)
  const create = (data: Location) => post<Location>("/depots", data)
  const update = (id: number, data: Location) => put<Location>(`/depots/${id}`, data)
  const remove = (id: number) => del(`/depots/${id}`)

  return { getAll, getOne, create, update, remove }
}
