import type { Asset, AssetScores, Downtime, Inspection, AssetPM, PurchaseOrder, WorkOrder } from "~/types"

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

  return {
    getAll, getOne, getByLocation, create, update, remove,
    getDowntimes, getWorkOrders, getInspections, getPurchaseOrders, getAssetPMs,
    getScoreByAsset, createScore, updateScore, removeScore,
  }
}
