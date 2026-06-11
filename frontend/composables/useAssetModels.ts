import type { AssetModel } from "~/types"

export function useAssetModels() {
  const { get, post, put, del } = useApi()

  const getAll = () => get<AssetModel[]>("/asset-models")
  const getOne = (modelNo: string) => get<AssetModel>(`/asset-models/${modelNo}`)
  const create = (data: AssetModel) => post<AssetModel>("/asset-models", data)
  const update = (modelNo: string, data: AssetModel) => put<AssetModel>(`/asset-models/${modelNo}`, data)
  const remove = (modelNo: string) => del(`/asset-models/${modelNo}`)

  return { getAll, getOne, create, update, remove }
}
