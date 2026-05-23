import type { Part, PartCategory, StockLevel, StockTransaction } from "~/types"

export function useInventory() {
  const { get, post, put, del } = useApi()

  const getParts = () => get<Part[]>("/inventory/parts")
  const getPart = (partNo: string) => get<Part>(`/inventory/parts/${partNo}`)
  const createPart = (data: Part) => post<Part>("/inventory/parts", data)
  const updatePart = (partNo: string, data: Part) => put<Part>(`/inventory/parts/${partNo}`, data)
  const removePart = (partNo: string) => del(`/inventory/parts/${partNo}`)

  const getCategories = () => get<PartCategory[]>("/inventory/part-categories")
  const createCategory = (data: PartCategory) => post<PartCategory>("/inventory/part-categories", data)

  const getStockLevels = () => get<StockLevel[]>("/inventory/stock-levels")
  const createStockLevel = (data: StockLevel) => post<StockLevel>("/inventory/stock-levels", data)
  const updateStockLevel = (id: number, data: StockLevel) => put<StockLevel>(`/inventory/stock-levels/${id}`, data)

  const getTransactions = () => get<StockTransaction[]>("/inventory/stock-transactions")
  const createTransaction = (data: StockTransaction) => post<StockTransaction>("/inventory/stock-transactions", data)

  return {
    getParts, getPart, createPart, updatePart, removePart,
    getCategories, createCategory,
    getStockLevels, createStockLevel, updateStockLevel,
    getTransactions, createTransaction,
  }
}
