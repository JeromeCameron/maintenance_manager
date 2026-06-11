import type { AssetPM, PmPlans } from "~/types"

export function useMaintenance() {
  const { get, post, put, del } = useApi()

  const getAllPMs = () => get<AssetPM[]>("/maintenance/asset-pms")
  const getPM = (id: number) => get<AssetPM>(`/maintenance/asset-pms/${id}`)
  const getPMsByAsset = (assetId: string) => get<AssetPM[]>(`/maintenance/asset-pms/asset/${assetId}`)
  const createPM = (data: AssetPM) => post<AssetPM>("/maintenance/asset-pms", data)
  const updatePM = (id: number, data: AssetPM) => put<AssetPM>(`/maintenance/asset-pms/${id}`, data)
  const removePM = (id: number) => del(`/maintenance/asset-pms/${id}`)

  const getPlans = () => get<PmPlans[]>("/maintenance/pm-plans")
  const getPlan = (id: string) => get<PmPlans>(`/maintenance/pm-plans/${id}`)
  const createPlan = (data: PmPlans) => post<PmPlans>("/maintenance/pm-plans", data)
  const updatePlan = (id: string, data: PmPlans) => put<PmPlans>(`/maintenance/pm-plans/${id}`, data)
  const removePlan = (id: string) => del(`/maintenance/pm-plans/${id}`)

  return { getAllPMs, getPM, getPMsByAsset, createPM, updatePM, removePM, getPlans, getPlan, createPlan, updatePlan, removePlan }
}
