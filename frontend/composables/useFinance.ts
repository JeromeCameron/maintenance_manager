import type { PurchaseOrder, Invoice, Budget, CostCentre } from "~/types"

export function useFinance() {
  const { get, post, put, del } = useApi()

  const getPOs = () => get<PurchaseOrder[]>("/purchase-orders")
  const getPOsBySupplier = (supplierId: number) => get<PurchaseOrder[]>(`/purchase-orders/supplier/${supplierId}`)
  const getPO = (poNo: string) => get<PurchaseOrder>(`/purchase-orders/${poNo}`)
  const createPO = (data: PurchaseOrder) => post<PurchaseOrder>("/purchase-orders", data)
  const updatePO = (poNo: string, data: PurchaseOrder) => put<PurchaseOrder>(`/purchase-orders/${poNo}`, data)
  const removePO = (poNo: string) => del(`/purchase-orders/${poNo}`)

  const getInvoices = () => get<Invoice[]>("/invoices")
  const getInvoicesBySupplier = (supplierId: number) => get<Invoice[]>(`/invoices/supplier/${supplierId}`)
  const getInvoice = (id: number) => get<Invoice>(`/invoices/${id}`)
  const createInvoice = (data: Invoice) => post<Invoice>("/invoices", data)
  const updateInvoice = (id: number, data: Invoice) => put<Invoice>(`/invoices/${id}`, data)
  const removeInvoice = (id: number) => del(`/invoices/${id}`)

  const getBudgets = () => get<Budget[]>("/budgets")
  const createBudget = (data: Budget) => post<Budget>("/budgets", data)
  const updateBudget = (id: number, data: Budget) => put<Budget>(`/budgets/${id}`, data)
  const removeBudget = (id: number) => del(`/budgets/${id}`)

  const getCostCentres = () => get<CostCentre[]>("/cost-centres")
  const createCostCentre = (data: CostCentre) => post<CostCentre>("/cost-centres", data)
  const updateCostCentre = (glCode: string, data: CostCentre) => put<CostCentre>(`/cost-centres/${glCode}`, data)
  const removeCostCentre = (glCode: string) => del(`/cost-centres/${glCode}`)

  return {
    getPOs, getPO, getPOsBySupplier, createPO, updatePO, removePO,
    getInvoices, getInvoicesBySupplier, getInvoice, createInvoice, updateInvoice, removeInvoice,
    getBudgets, createBudget, updateBudget, removeBudget,
    getCostCentres, createCostCentre, updateCostCentre, removeCostCentre,
  }
}
