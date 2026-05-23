import type { Supplier } from "~/types"

export function useSuppliers() {
  const { get, post, put, del } = useApi()

  const getAll = () => get<Supplier[]>("/suppliers")
  const getOne = (id: number) => get<Supplier>(`/suppliers/${id}`)
  const create = (data: Supplier) => post<Supplier>("/suppliers", data)
  const update = (id: number, data: Supplier) => put<Supplier>(`/suppliers/${id}`, data)
  const remove = (id: number) => del(`/suppliers/${id}`)

  return { getAll, getOne, create, update, remove }
}
