// Enums
export type AssetCategory = "baler" | "conveyor" | "bobcat" | "forklift" | "scale"
export type AssetStatus = "operational" | "maintenance" | "disposed" | "out_of_service"
export type AssetSubStatus = "watch_list" | "limited_duty" | "pending_inspection" | "in_repair" | "awaiting_parts"
export type AssetOwnership = "owned" | "rented" | "leased"
export type WorkOrderStatus = "requested" | "scheduled" | "awaiting_parts" | "awaiting_po" | "in_progress" | "on_hold" | "cancelled" | "completed" | "closed"
export type InvoiceStatus = "processing" | "submitted" | "on_hold"
export type InvoiceType = "parts" | "parts_and_labour" | "labour" | "consumables" | "services"
export type PurchaseOrderType = "corrective" | "predictive" | "preventative" | "consumables" | "rental"
export type TransactionType = "issue" | "receive" | "adjust"
export type UnitMeasure = "unit" | "pieces" | "gallons" | "drums" | "boxes" | "pairs" | "quart" | "liter" | "meter" | "bag"
export type LocationType = "redemption_centre" | "depot"
export type InspectionFrequency = "daily" | "weekly" | "monthly"
export type InspectionItemResult = "pass" | "fail" | "na"
export type PmFrequency = "annually" | "biannually" | "quarterly" | "every_four_month" | "every_other_month" | "monthly" | "fortnightly" | "weekly" | "daily"
export type PmTrigger = "operating_hours" | "calendar_based"
export type IssueSeverity = "low" | "medium" | "high" | "critical"
export type IssueStatus = "open" | "in_review" | "converted" | "dismissed"
export type PmOwner = "operator" | "maintenance_team" | "coantactor"

// Models
export interface Holiday {
  holiday_id?: number
  name: string
  holiday_date: string
}

export interface Asset {
  asset_id: string
  manufacturer: string
  model_no?: string
  yr?: number
  serial_no?: string
  category: AssetCategory
  owned: AssetOwnership
  alias?: string
  date_in_service?: string
  status: AssetStatus
  sub_status?: AssetSubStatus
  notes?: string
  location_id?: number
}

export interface AssetModel {
  model_no: string
  manufacturer: string
  category?: AssetCategory
  description?: string
  bale_weight?: number
  bale_time?: number
  ram_force?: number
  bale_size?: string
  baler_type?: "vertical" | "horizontal"
  baler_size?: "small" | "medium" | "large"
}

export interface AssetScores {
  score_id?: number
  asset_id?: string
  operational_score?: number
  safety_score?: number
  backup_score?: number
  repair_score?: number
  usage_score?: number
}

export interface Location {
  location_id?: number
  name: string
  parish: string
  supervisor: string
  contact_no: string
  shift_depot?: boolean
  shift_length?: number
  latitude?: string
  longitude?: string
  typ: LocationType
}

export interface Downtime {
  downtime_id?: number
  log_date?: string
  asset_id?: string
  shift_asset?: boolean
  cause_id?: number
  start_date?: string
  start_time?: string
  end_date?: string
  end_time?: string
  planned?: boolean
  details?: string
  component_affected?: string
  root_cause?: string
  corrective_action?: string
  repeat_failure?: boolean
  temporary_fix?: boolean
  work_order: string
  downtime_hours?: number
}

export interface DowntimeCause {
  cause_id?: number
  name: string
  description?: string
  active: boolean
}

export interface WorkOrder {
  work_order_id?: number
  issue_date?: string
  priority: string
  typ: string
  asset_id?: string
  asset_pm_id?: number
  description?: string
  supplier_id?: number
  expected_date?: string
  date_completed?: string
  start_time?: string
  end_time?: string
  notes?: string
  status: WorkOrderStatus
  estimated_cost?: number
  estimated_hours?: number
  actual_cost?: number
  actual_hours?: number
  planned?: boolean
}

export interface WorkOrderPart {
  id?: number
  work_order_id?: number
  part_no?: string
  quantity_used: number
  unit_cost?: number
  total_cost?: number
}

export interface Supplier {
  supplier_id?: number
  name: string
  address: string
  primary_contact: string
  email: string
  contact_number?: string
  contact_title?: string
  notes?: string
  categories?: string[]
}

export interface Invoice {
  id?: number
  invoice_no: string
  invoice_date?: string
  job_date?: string
  rec_date?: string
  supplier_id?: number
  work_order_id?: number
  asset_id?: string
  location_id?: number
  description?: string
  po_no?: string
  subtotal: number
  status: InvoiceStatus
  tax_cert?: boolean
  invoice_type: InvoiceType
}

export interface PurchaseOrder {
  po_no: string
  po_date?: string
  supplier_id?: number
  asset_id?: string
  location_id?: number
  description?: string
  subtotal: number
  po_type: PurchaseOrderType
  cost_centre_id?: string
}

export interface CostCentre {
  gl_code: string
  description?: string
  location_id?: number
}

export interface Budget {
  id?: number
  gl_code?: string
  financial_year: string
  month: string
  amount: number
  notes?: string
}

export interface Part {
  part_no: string
  part_name: string
  manufacturer?: string
  description?: string
  category_id?: number
  unit_of_measure: UnitMeasure
  min_level: number
  max_level: number
  reorder_level: number
  reorder_qty: number
  last_cost?: number
  is_critical?: boolean
  is_active?: boolean
}

export interface PartCategory {
  id?: number
  name: string
}

export interface EquipmentPart {
  id?: number
  model_no?: string
  part_no?: string
  is_critical?: boolean
}

export interface PartSupplier {
  id?: number
  part_no?: string
  supplier_id?: number
  supplier_part_no?: string
  last_cost?: number
  lead_time_days?: number
}

export interface StockLevel {
  id?: number
  part_no?: string
  location_id?: number
  quantity: number
  last_updated?: string
}

export interface StockTransaction {
  id?: number
  part_no?: string
  location_id?: number
  transaction_type: TransactionType
  quantity: number
  transaction_date?: string
  work_order_id?: number
  po_no?: string
  entered_by?: number
  notes?: string
}

export interface PmPlans {
  pm_id: string
  asset_type: AssetCategory
  trigger: PmTrigger
  frequency: PmFrequency
  description?: string
  owner: PmOwner
  notes?: string
}

export interface AssetPM {
  id?: number
  asset_id?: string
  pm_plan_id?: string
  last_service?: string
  next_service?: string
  active: boolean
}

export interface InspectionTemplate {
  id?: number
  name: string
  asset_type: AssetCategory
  frequency: InspectionFrequency
  active: boolean
  notes?: string
}

export interface InspectionTemplateItem {
  id?: number
  template_id?: number
  question: string
  category?: string
  is_critical: boolean
  order?: number
}

export interface InspectionResult {
  id?: number
  inspection_id?: number
  template_item_id?: number
  result: InspectionItemResult
  notes?: string
  work_order_id?: number
}

export interface Inspection {
  id?: number
  inspection_no: string
  asset_id?: string
  template_id?: number
  inspected_by?: number
  inspection_date: string
  inspection_time?: string
  overall_result: InspectionItemResult
  submitted: boolean
  submitted_date?: string
  notes?: string
}

export interface Issue {
  id?: number
  asset_id?: string
  reported_by?: number
  reported_at?: string
  description: string
  severity: IssueSeverity
  status: IssueStatus
  work_order_id?: number
}

export interface User {
  id?: number
  username: string
  firstname: string
  lastname: string
  role: "admin" | "user" | "moderator"
  email: string
  password: string
  active: boolean
}
