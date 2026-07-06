import type { Asset, AssetScores, AssetShiftHistory, Downtime, Inspection, AssetPM, PurchaseOrder, WorkOrder } from "~/types"

export function useAssets() {
  const { get, post, put, del } = useApi()

  const getAll = () => get<Asset[]>("/assets")
  const getOne = (id: string) => get<Asset>(`/assets/${id}`)
  const getByLocation = (locationId: number) => get<Asset[]>(`/assets/location/${locationId}`)
  const create = (data: Asset) => post<Asset>("/assets", data)
  const update = (id: string, data: Asset) => put<Asset>(`/assets/${id}`, data)
  const remove = (id: string) => del(`/assets/${id}`)

  const getDowntimes = (assetId: string) => get<Downtime[]>(`/downtimes/asset/${assetId}`)
  const getWorkOrders = (assetId: string) => get<WorkOrder[]>(`/work-orders/asset/${assetId}`)
  const getInspections = (assetId: string) => get<Inspection[]>(`/inspections/asset/${assetId}`)
  const getPurchaseOrders = (assetId: string) => get<PurchaseOrder[]>(`/purchase-orders/asset/${assetId}`)
  const getAssetPMs = (assetId: string) => get<AssetPM[]>(`/maintenance/asset-pms/asset/${assetId}`)

  // Asset Scores
  const getScoreByAsset = (assetId: string) => get<AssetScores | null>(`/asset-scores/asset/${assetId}`)
  const createScore = (data: AssetScores) => post<AssetScores>("/asset-scores", data)
  const updateScore = (scoreId: number, data: AssetScores) => put<AssetScores>(`/asset-scores/${scoreId}`, data)
  const removeScore = (scoreId: number) => del(`/asset-scores/${scoreId}`)

  interface Availability30d { availability: number; downtime_hours: number; scheduled_hours: number }
  const getAvailability30d = (assetId: string) => get<Availability30d>(`/downtimes/availability-30d/${assetId}`)

  // Asset Shift History
  const getShiftHistory = (assetId: string) => get<AssetShiftHistory[]>(`/assets/${assetId}/shift-history`)
  const createShiftHistory = (assetId: string, data: AssetShiftHistory) => post<AssetShiftHistory>(`/assets/${assetId}/shift-history`, data)
  const updateShiftHistory = (id: number, data: AssetShiftHistory) => put<AssetShiftHistory>(`/asset-shift-history/${id}`, data)
  const removeShiftHistory = (id: number) => del(`/asset-shift-history/${id}`)

  return {
    getAll, getOne, getByLocation, create, update, remove,
    getDowntimes, getWorkOrders, getInspections, getPurchaseOrders, getAssetPMs,
    getScoreByAsset, createScore, updateScore, removeScore,
    getShiftHistory, createShiftHistory, updateShiftHistory, removeShiftHistory,
    getAvailability30d,
  }
}
