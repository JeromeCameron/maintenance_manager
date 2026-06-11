import type { Inspection, InspectionTemplate, InspectionTemplateItem, InspectionResult } from "~/types"

export function useInspections() {
  const { get, post, put, del } = useApi()

  // Inspections
  const getAll = () => get<Inspection[]>("/inspections")
  const getOne = (id: number) => get<Inspection>(`/inspections/${id}`)
  const getByAsset = (assetId: string) => get<Inspection[]>(`/inspections/asset/${assetId}`)
  const create = (data: Inspection) => post<Inspection>("/inspections", data)
  const update = (id: number, data: Inspection) => put<Inspection>(`/inspections/${id}`, data)
  const remove = (id: number) => del(`/inspections/${id}`)

  // Templates
  const getTemplates = () => get<InspectionTemplate[]>("/inspection-templates")
  const getTemplate = (id: number) => get<InspectionTemplate>(`/inspection-templates/${id}`)
  const createTemplate = (data: InspectionTemplate) => post<InspectionTemplate>("/inspection-templates", data)
  const updateTemplate = (id: number, data: InspectionTemplate) => put<InspectionTemplate>(`/inspection-templates/${id}`, data)
  const removeTemplate = (id: number) => del(`/inspection-templates/${id}`)

  // Template Items
  const getItemsByTemplate = (templateId: number) => get<InspectionTemplateItem[]>(`/inspection-template-items/template/${templateId}`)
  const createItem = (data: InspectionTemplateItem) => post<InspectionTemplateItem>("/inspection-template-items", data)
  const updateItem = (id: number, data: InspectionTemplateItem) => put<InspectionTemplateItem>(`/inspection-template-items/${id}`, data)
  const removeItem = (id: number) => del(`/inspection-template-items/${id}`)

  // Results
  const getResultsByInspection = (inspectionId: number) => get<InspectionResult[]>(`/inspection-results/inspection/${inspectionId}`)
  const createResult = (data: InspectionResult) => post<InspectionResult>("/inspection-results", data)
  const updateResult = (id: number, data: InspectionResult) => put<InspectionResult>(`/inspection-results/${id}`, data)
  const removeResult = (id: number) => del(`/inspection-results/${id}`)

  return {
    getAll, getOne, getByAsset, create, update, remove,
    getTemplates, getTemplate, createTemplate, updateTemplate, removeTemplate,
    getItemsByTemplate, createItem, updateItem, removeItem,
    getResultsByInspection, createResult, updateResult, removeResult,
  }
}
