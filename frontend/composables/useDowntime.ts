import type { Downtime, DowntimeCause } from "~/types"

export function useDowntime() {
  const { get, post, put, del } = useApi()

  const getAll = () => get<Downtime[]>("/downtimes")
  const getOne = (id: number) => get<Downtime>(`/downtimes/${id}`)
  const getByAsset = (assetId: string) => get<Downtime[]>(`/downtimes/asset/${assetId}`)
  const create = (data: Downtime) => post<Downtime>("/downtimes", data)
  const update = (id: number, data: Downtime) => put<Downtime>(`/downtimes/${id}`, data)
  const remove = (id: number) => del(`/downtimes/${id}`)

  const getCauses = () => get<DowntimeCause[]>("/downtime-causes")
  const createCause = (data: DowntimeCause) => post<DowntimeCause>("/downtime-causes", data)
  const updateCause = (id: number, data: DowntimeCause) => put<DowntimeCause>(`/downtime-causes/${id}`, data)
  const removeCause = (id: number) => del(`/downtime-causes/${id}`)

  return { getAll, getOne, getByAsset, create, update, remove, getCauses, createCause, updateCause, removeCause }
}
