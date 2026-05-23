import type { Asset, Downtime, Inspection, AssetPM, PurchaseOrder, WorkOrder } from "~/types"

export function useAssets() {
  const { get, post, put, del } = useApi()

  const getAll = () => get<Asset[]>("/assets")
  const getOne = (id: string) => get<Asset>(`/assets/${id}`)
  const create = (data: Asset) => post<Asset>("/assets", data)
  const update = (id: string, data: Asset) => put<Asset>(`/assets/${id}`, data)
  const remove = (id: string) => del(`/assets/${id}`)

  const getDowntimes = (assetId: string) => get<Downtime[]>(`/downtimes/asset/${assetId}`)
  const getWorkOrders = (assetId: string) => get<WorkOrder[]>(`/work-orders/asset/${assetId}`)
  const getInspections = (assetId: string) => get<Inspection[]>(`/inspections/asset/${assetId}`)
  const getPurchaseOrders = (assetId: string) => get<PurchaseOrder[]>(`/purchase-orders/asset/${assetId}`)
  const getAssetPMs = (assetId: string) => get<AssetPM[]>(`/maintenance/asset-pms/asset/${assetId}`)

  return { getAll, getOne, create, update, remove, getDowntimes, getWorkOrders, getInspections, getPurchaseOrders, getAssetPMs }
}
