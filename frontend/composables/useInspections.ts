import type { Inspection, InspectionTemplate } from "~/types"

export function useInspections() {
  const { get, post, put, del } = useApi()

  const getAll = () => get<Inspection[]>("/inspections")
  const getOne = (id: number) => get<Inspection>(`/inspections/${id}`)
  const getByAsset = (assetId: string) => get<Inspection[]>(`/inspections/asset/${assetId}`)
  const create = (data: Inspection) => post<Inspection>("/inspections", data)
  const update = (id: number, data: Inspection) => put<Inspection>(`/inspections/${id}`, data)
  const remove = (id: number) => del(`/inspections/${id}`)

  const getTemplates = () => get<InspectionTemplate[]>("/inspection-templates")
  const createTemplate = (data: InspectionTemplate) => post<InspectionTemplate>("/inspection-templates", data)

  return { getAll, getOne, getByAsset, create, update, remove, getTemplates, createTemplate }
}
