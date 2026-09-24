import type { Downtime, DowntimeCause, DowntimeFactor, DowntimeFactorType } from "~/types"

export interface DowntimeFactorSummaryRow {
  month: string
  factor_type: string
  delay_hours: number
  events: number
}

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

  // ── Exacerbating factors ───────────────────────────────────────
  const getFactorTypes = () => get<DowntimeFactorType[]>("/downtime-factor-types")
  const createFactorType = (data: DowntimeFactorType) => post<DowntimeFactorType>("/downtime-factor-types", data)
  const updateFactorType = (id: number, data: DowntimeFactorType) => put<DowntimeFactorType>(`/downtime-factor-types/${id}`, data)
  const removeFactorType = (id: number) => del(`/downtime-factor-types/${id}`)

  const getFactors = () => get<DowntimeFactor[]>("/downtime-factors")
  const getFactorsByDowntime = (downtimeId: number) => get<DowntimeFactor[]>(`/downtime-factors/downtime/${downtimeId}`)
  const createFactor = (data: DowntimeFactor) => post<DowntimeFactor>("/downtime-factors", data)
  const updateFactor = (id: number, data: DowntimeFactor) => put<DowntimeFactor>(`/downtime-factors/${id}`, data)
  const removeFactor = (id: number) => del(`/downtime-factors/${id}`)

  const getFactorSummary = (months = 12) =>
    get<DowntimeFactorSummaryRow[]>(`/downtimes/factor-summary?months=${months}`)

  return {
    getAll, getOne, getByAsset, create, update, remove,
    getCauses, createCause, updateCause, removeCause,
    getFactorTypes, createFactorType, updateFactorType, removeFactorType,
    getFactors, getFactorsByDowntime, createFactor, updateFactor, removeFactor,
    getFactorSummary,
  }
}
