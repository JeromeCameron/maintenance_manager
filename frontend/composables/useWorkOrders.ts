import type { WorkOrder, WorkOrderPart } from "~/types"

export function useWorkOrders() {
  const { get, post, put, del } = useApi()

  const getAll = () => get<WorkOrder[]>("/work-orders")
  const getOne = (id: number) => get<WorkOrder>(`/work-orders/${id}`)
  const create = (data: WorkOrder) => post<WorkOrder>("/work-orders", data)
  const update = (id: number, data: WorkOrder) => put<WorkOrder>(`/work-orders/${id}`, data)
  const remove = (id: number) => del(`/work-orders/${id}`)

  const getParts = () => get<WorkOrderPart[]>("/work-order-parts")
  const addPart = (data: WorkOrderPart) => post<WorkOrderPart>("/work-order-parts", data)
  const removePart = (id: number) => del(`/work-order-parts/${id}`)

  return { getAll, getOne, create, update, remove, getParts, addPart, removePart }
}
