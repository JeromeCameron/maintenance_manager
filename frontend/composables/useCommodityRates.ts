export interface CommodityRate {
  id?: number
  effective_date: string
  rate_per_lb: number
  notes?: string
}

export function useCommodityRates() {
  const { get, post, put, del } = useApi()

  const getAll = () => get<CommodityRate[]>("/commodity-rates")
  const create = (data: CommodityRate) => post<CommodityRate>("/commodity-rates", data)
  const update = (id: number, data: CommodityRate) => put<CommodityRate>(`/commodity-rates/${id}`, data)
  const remove = (id: number) => del(`/commodity-rates/${id}`)

  return { getAll, create, update, remove }
}
