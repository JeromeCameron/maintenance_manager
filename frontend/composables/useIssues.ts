import type { Issue } from "~/types"

export function useIssues() {
  const { get, post, put, del } = useApi()

  const getAll = () => get<Issue[]>("/issues")
  const getOne = (id: number) => get<Issue>(`/issues/${id}`)
  const getByAsset = (assetId: string) => get<Issue[]>(`/issues/asset/${assetId}`)
  const create = (data: Issue) => post<Issue>("/issues", data)
  const update = (id: number, data: Partial<Issue>) => put<Issue>(`/issues/${id}`, data)
  const remove = (id: number) => del(`/issues/${id}`)

  return { getAll, getOne, getByAsset, create, update, remove }
}
