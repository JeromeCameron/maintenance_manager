import type { Part, PartCategory, EquipmentPart, PartSupplier, StockLevel, StockTransaction } from "~/types"

export function useInventory() {
  const { get, post, put, del } = useApi()

  // Parts
  const getParts = () => get<Part[]>("/inventory/parts")
  const getPart = (partNo: string) => get<Part>(`/inventory/parts/${partNo}`)
  const createPart = (data: Part) => post<Part>("/inventory/parts", data)
  const updatePart = (partNo: string, data: Part) => put<Part>(`/inventory/parts/${partNo}`, data)
  const removePart = (partNo: string) => del(`/inventory/parts/${partNo}`)

  // Part Categories
  const getCategories = () => get<PartCategory[]>("/inventory/part-categories")
  const createCategory = (data: PartCategory) => post<PartCategory>("/inventory/part-categories", data)
  const updateCategory = (id: number, data: PartCategory) => put<PartCategory>(`/inventory/part-categories/${id}`, data)
  const removeCategory = (id: number) => del(`/inventory/part-categories/${id}`)

  // Equipment Parts
  const getEquipmentPartsByPart = (partNo: string) => get<EquipmentPart[]>(`/inventory/equipment-parts/part/${partNo}`)
  const createEquipmentPart = (data: EquipmentPart) => post<EquipmentPart>("/inventory/equipment-parts", data)
  const updateEquipmentPart = (id: number, data: EquipmentPart) => put<EquipmentPart>(`/inventory/equipment-parts/${id}`, data)
  const removeEquipmentPart = (id: number) => del(`/inventory/equipment-parts/${id}`)

  // Part Suppliers
  const getPartSuppliersByPart = (partNo: string) => get<PartSupplier[]>(`/inventory/part-suppliers/part/${partNo}`)
  const createPartSupplier = (data: PartSupplier) => post<PartSupplier>("/inventory/part-suppliers", data)
  const updatePartSupplier = (id: number, data: PartSupplier) => put<PartSupplier>(`/inventory/part-suppliers/${id}`, data)
  const removePartSupplier = (id: number) => del(`/inventory/part-suppliers/${id}`)

  // Stock Levels
  const getStockLevels = () => get<StockLevel[]>("/inventory/stock-levels")
  const createStockLevel = (data: StockLevel) => post<StockLevel>("/inventory/stock-levels", data)
  const updateStockLevel = (id: number, data: StockLevel) => put<StockLevel>(`/inventory/stock-levels/${id}`, data)
  const removeStockLevel = (id: number) => del(`/inventory/stock-levels/${id}`)

  // Stock Transactions
  const getTransactions = () => get<StockTransaction[]>("/inventory/stock-transactions")
  const createTransaction = (data: StockTransaction) => post<StockTransaction>("/inventory/stock-transactions", data)
  const updateTransaction = (id: number, data: StockTransaction) => put<StockTransaction>(`/inventory/stock-transactions/${id}`, data)
  const removeTransaction = (id: number) => del(`/inventory/stock-transactions/${id}`)

  return {
    getParts, getPart, createPart, updatePart, removePart,
    getCategories, createCategory, updateCategory, removeCategory,
    getEquipmentPartsByPart, createEquipmentPart, updateEquipmentPart, removeEquipmentPart,
    getPartSuppliersByPart, createPartSupplier, updatePartSupplier, removePartSupplier,
    getStockLevels, createStockLevel, updateStockLevel, removeStockLevel,
    getTransactions, createTransaction, updateTransaction, removeTransaction,
  }
}
