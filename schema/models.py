from datetime import date, datetime, time
from enum import Enum
from typing import ClassVar, List, Optional

from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy import CheckConstraint, Text
from sqlmodel import Field, Relationship, SQLModel


class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    moderator = "moderator"


class AssetCategory(str, Enum):
    baler = "baler"
    conveyor = "conveyor"
    bobcat = "bobcat"
    forklift = "forklift"
    scale = "scale"


class AssetOwnership(str, Enum):
    owned = "owned"
    rented = "rented"
    leased = "leased"


class AssetStatus(str, Enum):
    operational = "operational"
    maintenance = "maintenance"
    disposed = "disposed"
    out_of_service = "out_of_service"
    retired = "retired"


class AssetSubStatus(str, Enum):
    watch_list = "watch_list"
    limited_duty = "limited_duty"
    pending_inspection = "pending_inspection"
    in_repair = "in_repair"
    awaiting_parts = "awaiting_parts"


class BalerType(str, Enum):
    vertical = "vertical"
    horizontal = "horizontal"


class BalerSize(str, Enum):
    small = "small"
    medium = "medium"
    large = "large"


class LocationType(str, Enum):
    redemption_centre = "redemption_centre"
    depot = "depot"


class WorkOrderStatus(str, Enum):
    requested = "requested"
    scheduled = "scheduled"
    awaiting_parts = "awaiting_parts"
    awaiting_po = "awaiting_po"
    in_progress = "in_progress"
    on_hold = "on_hold"
    cancelled = "cancelled"
    completed = "completed"
    closed = "closed"


class SupplierCategory(str, Enum):
    parts = "parts"
    services = "services"
    rental = "rental"
    safety_gears = "safety_gears"


class InvoiceType(str, Enum):
    parts = "parts"
    parts_and_labour = "parts_and_labour"
    labour = "labour"
    consumables = "consumables"
    services = "services"


class InvoiceStatus(str, Enum):
    processing = "processing"
    submitted = "submitted"
    on_hold = "on_hold"


class PurchaseOrderType(str, Enum):
    corrective = "corrective"
    predictive = "predictive"
    preventative = "preventative"
    consumables = "consumables"
    rental = "rental"
    purchase = "purchase"


class TransactionType(str, Enum):
    issue = "issue"
    receive = "receive"
    adjust = "adjust"


class UnitMeasure(str, Enum):
    unit = "unit"
    pieces = "pieces"
    gallons = "gallons"
    drums = "drums"
    boxes = "boxes"
    pairs = "pairs"
    quart = "quart"
    liter = "liter"
    meter = "meter"
    bag = "bag"


class PmTriggers(str, Enum):
    operating_hours = "operating_hours"
    calendar_based = "calendar_based"


class PmOwner(str, Enum):
    operator = "operator"
    maintenance_team = "maintenance_team"
    contractor = "contractor"


class PmFrequency(str, Enum):
    annually = "annually"
    biannually = "biannually"
    quarterly = "quarterly"
    every_four_month = "every_four_month"
    every_other_month = "every_other_month"
    monthly = "monthly"
    fortnightly = "fortnightly"
    weekly = "weekly"
    daily = "daily"


class InspectionFrequency(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class InspectionItemResult(str, Enum):
    pass_ = "pass"
    fail = "fail"
    na = "na"


class IssueSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IssueStatus(str, Enum):
    open = "open"
    in_review = "in_review"
    converted = "converted"
    dismissed = "dismissed"


# ----------------------------------------------------------------------------- #


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    firstname: str
    lastname: str
    role: UserRole = Field(default=UserRole.user)
    email: str = Field(unique=True)
    password: str
    active: bool = Field(default=True)
    first_login: Optional[datetime] = Field(default=None)
    last_login: Optional[datetime] = Field(default=None)

    stock_transactions: List["StockTransaction"] = Relationship(
        back_populates="entered_by_user"
    )
    inspections: List["Inspection"] = Relationship(back_populates="inspector")
    issues: List["Issue"] = Relationship(back_populates="reporter")


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    username: str
    firstname: str
    lastname: str
    role: UserRole
    email: str
    active: bool
    first_login: Optional[datetime] = None
    last_login: Optional[datetime] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ReactivityStats(BaseModel):
    total: int
    planned: int
    unplanned: int
    planned_pct: float
    unplanned_pct: float


class ReactivityTrendMonth(BaseModel):
    month: str
    total: int
    planned: int
    unplanned: int
    planned_pct: float
    unplanned_pct: float


# ------------- Utility Tables ----------------------- #
class Holidays(SQLModel, table=True):
    holiday_id: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    name: str
    holiday_date: date


# ------------- Asset Managment ----------------------- #
class AssetModel(SQLModel, table=True):
    model_no: str = Field(primary_key=True, nullable=False)
    manufacturer: str
    category: AssetCategory = Field(default=None)
    description: Optional[str] = Field(default=None, sa_type=Text)
    # Baler specs (populated when category = baler)
    bale_weight: Optional[int] = Field(default=None)
    bale_time: Optional[int] = Field(default=None)
    ram_force: Optional[int] = Field(default=None)
    bale_size: Optional[str] = Field(default=None)
    baler_type: Optional[BalerType] = Field(default=None)
    baler_size: Optional[BalerSize] = Field(default=None)

    assets: List["Asset"] = Relationship(back_populates="model")
    equipment_parts: List["EquipmentPart"] = Relationship(back_populates="model")


# add nickname field
class Asset(SQLModel, table=True):
    asset_id: Optional[str] = Field(primary_key=True, nullable=False)
    manufacturer: str
    model_no: Optional[str] = Field(default=None, foreign_key="assetmodel.model_no")
    yr: Optional[int] = Field(default=None)
    serial_no: Optional[str] = Field(default=None)
    category: AssetCategory = Field(default=None)
    owned: AssetOwnership = Field(default=AssetOwnership.owned)
    alias: Optional[str] = Field(default=None)  # New
    date_in_service: Optional[date] = Field(default=None)
    status: AssetStatus = Field(default=AssetStatus.operational)
    sub_status: Optional[AssetSubStatus] = Field(default=None)
    notes: Optional[str] = Field(default=None, sa_type=Text)
    location_id: Optional[int] = Field(default=None, foreign_key="location.location_id")

    location: Optional["Location"] = Relationship(back_populates="assets")
    downtimes: List["Downtime"] = Relationship(back_populates="asset")
    work_orders: List["WorkOrder"] = Relationship(back_populates="asset")
    scores: Optional["AssetScores"] = Relationship(back_populates="asset")
    asset_pms: List["AssetPM"] = Relationship(back_populates="asset")
    model: Optional["AssetModel"] = Relationship(back_populates="assets")
    inspections: List["Inspection"] = Relationship(back_populates="asset")
    issues: List["Issue"] = Relationship(back_populates="asset")

    VALID_SUB_STATUSES: ClassVar[dict] = {
        AssetStatus.maintenance: [
            AssetSubStatus.in_repair,
            AssetSubStatus.awaiting_parts,
            AssetSubStatus.pending_inspection,
        ],
        AssetStatus.operational: [
            AssetSubStatus.watch_list,
            AssetSubStatus.limited_duty,
            AssetSubStatus.pending_inspection,
        ],
        AssetStatus.out_of_service: [
            AssetSubStatus.in_repair,
            AssetSubStatus.awaiting_parts,
            AssetSubStatus.pending_inspection,
        ],
    }

    @model_validator(mode="after")
    def validate_sub_status(self) -> "Asset":
        if self.sub_status is None:
            return self
        allowed = self.VALID_SUB_STATUSES.get(self.status, [])
        if self.sub_status not in allowed:
            raise ValueError(
                f"Sub-status '{self.sub_status}' is not valid for status '{self.status}'. "
                f"Allowed: {[s.value for s in allowed]}"
            )
        return self


class AssetScores(SQLModel, table=True):
    score_id: Optional[int] = Field(primary_key=True, default=None)
    asset_id: Optional[str] = Field(default=None, foreign_key="asset.asset_id")
    operational_score: Optional[int] = Field(default=None, ge=0, le=4)
    safety_score: Optional[int] = Field(default=None, ge=0, le=4)
    backup_score: Optional[int] = Field(default=None, ge=0, le=3)
    repair_score: Optional[int] = Field(default=None, ge=0, le=3)
    usage_score: Optional[int] = Field(default=None, ge=0, le=3)

    asset: Optional["Asset"] = Relationship(back_populates="scores")

    __table_args__ = (
        CheckConstraint(
            "operational_score BETWEEN 0 AND 4", name="chk_operational_score"
        ),
        CheckConstraint("safety_score BETWEEN 0 AND 4", name="chk_safety_score"),
        CheckConstraint("backup_score BETWEEN 0 AND 3", name="chk_backup_score"),
        CheckConstraint("repair_score BETWEEN 0 AND 3", name="chk_repair_score"),
        CheckConstraint("usage_score BETWEEN 0 AND 3", name="chk_usage_score"),
    )


class Location(SQLModel, table=True):
    location_id: Optional[int] = Field(primary_key=True, default=None)
    name: str
    parish: str
    supervisor: str
    contact_no: str
    shift_depot: Optional[bool] = Field(default=False)
    shift_length: Optional[int] = Field(default=8)
    latitude: Optional[str] = Field(default=None)
    longitude: Optional[str] = Field(default=None)
    typ: LocationType = Field(default=None)

    assets: List["Asset"] = Relationship(back_populates="location")
    invoices: List["Invoice"] = Relationship(back_populates="location")
    purchase_orders: List["PurchaseOrder"] = Relationship(back_populates="location")
    cost_centres: List["CostCentre"] = Relationship(back_populates="location")
    stock_levels: List["StockLevel"] = Relationship(back_populates="location")
    stock_transactions: List["StockTransaction"] = Relationship(
        back_populates="location"
    )


# ------------- Downtime Tracking ----------------------- #
class DowntimeCause(SQLModel, table=True):
    cause_id: Optional[int] = Field(primary_key=True, default=None)
    name: str = Field(unique=True)
    description: Optional[str] = Field(default=None)
    active: bool = Field(default=True)

    downtimes: List["Downtime"] = Relationship(back_populates="cause")


# Add shift_asset - if asset runs across multiple shifts
class Downtime(SQLModel, table=True):
    downtime_id: Optional[int] = Field(primary_key=True, default=None)
    log_date: Optional[datetime] = Field(default_factory=datetime.now)
    asset_id: Optional[str] = Field(default=None, foreign_key="asset.asset_id")
    shift_asset: bool  # New
    cause_id: Optional[int] = Field(default=None, foreign_key="downtimecause.cause_id")
    start_date: Optional[date] = Field(default=None)
    start_time: Optional[time] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    end_time: Optional[time] = Field(default=None)
    planned: Optional[bool] = Field(default=None)
    details: Optional[str] = Field(default=None, sa_type=Text)
    component_affected: Optional[str] = Field(default=None, sa_type=Text)
    root_cause: Optional[str] = Field(default=None, sa_type=Text)
    corrective_action: Optional[str] = Field(default=None, sa_type=Text)
    repeat_failure: Optional[bool] = Field(default=None)
    temporary_fix: Optional[bool] = Field(default=None)
    work_order: Optional[str] = Field(default=None)
    downtime_hours: Optional[float] = Field(default=None)

    asset: Optional["Asset"] = Relationship(back_populates="downtimes")
    cause: Optional["DowntimeCause"] = Relationship(back_populates="downtimes")


# ------------- Work Orders ----------------------- #
class WorkOrder(SQLModel, table=True):
    work_order_id: Optional[int] = Field(primary_key=True, default=None)
    issue_date: Optional[date] = Field(default=None)
    priority: str
    typ: str
    asset_id: Optional[str] = Field(default=None, foreign_key="asset.asset_id")
    asset_pm_id: Optional[int] = Field(default=None, foreign_key="assetpm.id")  # New
    description: Optional[str] = Field(default=None, sa_type=Text)
    supplier_id: Optional[int] = Field(default=None, foreign_key="supplier.supplier_id")
    expected_date: Optional[date] = Field(default=None)
    date_completed: Optional[date] = Field(default=None)
    start_time: Optional[time] = Field(default=None)
    end_time: Optional[time] = Field(default=None)
    notes: Optional[str] = Field(default=None, sa_type=Text)
    status: WorkOrderStatus = Field(default=WorkOrderStatus.requested)
    estimated_cost: Optional[float] = Field(default=None)
    estimated_hours: Optional[float] = Field(default=None)
    actual_cost: Optional[float] = Field(default=None)
    actual_hours: Optional[float] = Field(default=None)
    planned: Optional[bool] = Field(default=None)

    asset: Optional["Asset"] = Relationship(back_populates="work_orders")
    asset_pm: Optional["AssetPM"] = Relationship(back_populates="work_orders")
    supplier: Optional["Supplier"] = Relationship(back_populates="work_orders")
    invoices: List["Invoice"] = Relationship(back_populates="work_order")
    stock_transactions: List["StockTransaction"] = Relationship(
        back_populates="work_order"
    )
    inspection_results: List["InspectionResult"] = Relationship(
        back_populates="work_order"
    )
    parts_used: List["WorkOrderPart"] = Relationship(back_populates="work_order")
    issues: List["Issue"] = Relationship(back_populates="work_order")


class WorkOrderPart(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    work_order_id: Optional[int] = Field(
        default=None, foreign_key="workorder.work_order_id"
    )
    part_no: Optional[str] = Field(default=None, foreign_key="part.part_no")
    quantity_used: int
    unit_cost: Optional[float] = Field(default=None)
    total_cost: Optional[float] = Field(default=None)

    work_order: Optional["WorkOrder"] = Relationship(back_populates="parts_used")
    part: Optional["Part"] = Relationship(back_populates="work_order_usage")

    @model_validator(mode="after")
    def calculate_total_cost(self) -> "WorkOrderPart":
        if self.quantity_used is not None and self.unit_cost is not None:
            self.total_cost = round(self.quantity_used * self.unit_cost, 2)
        return self


# ------------- Issues ----------------------- #
class Issue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: Optional[str] = Field(default=None, foreign_key="asset.asset_id")
    reported_by: Optional[int] = Field(default=None, foreign_key="user.id")
    reported_at: Optional[datetime] = Field(default_factory=datetime.now)
    description: str = Field(sa_type=Text)
    severity: IssueSeverity
    status: IssueStatus = Field(default=IssueStatus.open)
    work_order_id: Optional[int] = Field(
        default=None, foreign_key="workorder.work_order_id"
    )

    asset: Optional["Asset"] = Relationship(back_populates="issues")
    reporter: Optional["User"] = Relationship(back_populates="issues")
    work_order: Optional["WorkOrder"] = Relationship(back_populates="issues")


# ------------- Supplier Managment ----------------------- #
class SupplierCategoryLink(SQLModel, table=True):
    supplier_id: Optional[int] = Field(
        default=None, foreign_key="supplier.supplier_id", primary_key=True
    )
    category: SupplierCategory = Field(primary_key=True)


class Supplier(SQLModel, table=True):
    supplier_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    address: str
    primary_contact: str
    email: str
    contact_number: Optional[str] = Field(default=None)
    contact_title: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None, sa_type=Text)

    categories: List["SupplierCategoryLink"] = Relationship()
    work_orders: List["WorkOrder"] = Relationship(back_populates="supplier")
    invoices: List["Invoice"] = Relationship(back_populates="supplier")
    purchase_orders: List["PurchaseOrder"] = Relationship(back_populates="supplier")
    parts: List["PartSupplier"] = Relationship(back_populates="supplier")


class SupplierInput(SQLModel):
    name: str
    address: str
    primary_contact: str
    email: str
    contact_number: Optional[str] = None
    contact_title: Optional[str] = None
    notes: Optional[str] = None
    categories: List[str] = []


class SupplierRead(SQLModel):
    supplier_id: Optional[int] = None
    name: str
    address: str
    primary_contact: str
    email: str
    contact_number: Optional[str] = None
    contact_title: Optional[str] = None
    notes: Optional[str] = None
    categories: List[str] = []


# ------------- Budget ----------------------- #
class Invoice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_no: str
    invoice_date: Optional[date] = Field(default=None)
    job_date: Optional[date] = Field(default=None)
    rec_date: Optional[date] = Field(default=None)
    supplier_id: Optional[int] = Field(default=None, foreign_key="supplier.supplier_id")
    work_order_id: Optional[int] = Field(
        default=None, foreign_key="workorder.work_order_id"
    )
    asset_id: Optional[str] = Field(default=None, foreign_key="asset.asset_id")
    location_id: Optional[int] = Field(default=None, foreign_key="location.location_id")
    description: Optional[str] = Field(default=None, sa_type=Text)
    po_no: Optional[str] = Field(default=None, foreign_key="purchaseorder.po_no")
    subtotal: float
    status: InvoiceStatus = Field(default=InvoiceStatus.processing)
    tax_cert: Optional[bool] = Field(default=False)
    invoice_type: InvoiceType = Field(default=None)

    location: Optional["Location"] = Relationship(back_populates="invoices")
    asset: Optional["Asset"] = Relationship()
    work_order: Optional["WorkOrder"] = Relationship(back_populates="invoices")
    supplier: Optional["Supplier"] = Relationship(back_populates="invoices")
    purchase_order: Optional["PurchaseOrder"] = Relationship(back_populates="invoices")


class PurchaseOrder(SQLModel, table=True):
    po_no: Optional[str] = Field(primary_key=True, nullable=False)
    po_date: Optional[date] = Field(default=None)
    supplier_id: Optional[int] = Field(default=None, foreign_key="supplier.supplier_id")
    asset_id: Optional[str] = Field(default=None, foreign_key="asset.asset_id")
    location_id: Optional[int] = Field(default=None, foreign_key="location.location_id")
    description: Optional[str] = Field(default=None, sa_type=Text)
    subtotal: float
    po_type: PurchaseOrderType = Field(default=None)
    cost_centre_id: Optional[str] = Field(
        default=None, foreign_key="costcentre.gl_code"
    )

    supplier: Optional["Supplier"] = Relationship(back_populates="purchase_orders")
    asset: Optional["Asset"] = Relationship()
    location: Optional["Location"] = Relationship(back_populates="purchase_orders")
    invoices: List["Invoice"] = Relationship(back_populates="purchase_order")


class CostCentre(SQLModel, table=True):
    gl_code: Optional[str] = Field(primary_key=True, nullable=False)
    description: Optional[str] = Field(default=None, sa_type=Text)
    location_id: Optional[int] = Field(default=None, foreign_key="location.location_id")

    location: Optional["Location"] = Relationship(back_populates="cost_centres")
    budgets: List["Budget"] = Relationship(back_populates="cost_centre")


class Budget(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    gl_code: Optional[str] = Field(default=None, foreign_key="costcentre.gl_code")
    financial_year: str
    month: date
    amount: float
    notes: Optional[str] = Field(default=None, sa_type=Text)

    cost_centre: Optional["CostCentre"] = Relationship(back_populates="budgets")


# ------------- Inventory ----------------------- #
class PartCategory(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    name: str = Field(unique=True)

    parts: List["Part"] = Relationship(back_populates="part_category")


class Part(SQLModel, table=True):
    part_no: str = Field(primary_key=True, nullable=False)
    part_name: str
    manufacturer: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None, sa_type=Text)
    category_id: Optional[int] = Field(default=None, foreign_key="partcategory.id")
    unit_of_measure: UnitMeasure = Field(default=None)
    min_level: int
    max_level: int
    reorder_level: int
    reorder_qty: int
    last_cost: Optional[float] = Field(default=None)
    is_critical: Optional[bool] = Field(default=False)
    is_active: Optional[bool] = Field(default=True)

    part_category: Optional["PartCategory"] = Relationship(back_populates="parts")
    suppliers: List["PartSupplier"] = Relationship(back_populates="part")
    equipment: List["EquipmentPart"] = Relationship(back_populates="part")
    transactions: List["StockTransaction"] = Relationship(back_populates="part")
    stock_levels: List["StockLevel"] = Relationship(back_populates="part")
    work_order_usage: List["WorkOrderPart"] = Relationship(back_populates="part")


class EquipmentPart(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    model_no: Optional[str] = Field(default=None, foreign_key="assetmodel.model_no")
    part_no: Optional[str] = Field(default=None, foreign_key="part.part_no")
    is_critical: Optional[bool] = Field(default=False)

    model: Optional["AssetModel"] = Relationship(back_populates="equipment_parts")
    part: Optional["Part"] = Relationship(back_populates="equipment")


class PartSupplier(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    part_no: Optional[str] = Field(default=None, foreign_key="part.part_no")
    supplier_id: Optional[int] = Field(default=None, foreign_key="supplier.supplier_id")
    supplier_part_no: Optional[str] = Field(default=None)
    last_cost: Optional[float] = Field(default=None)
    lead_time_days: Optional[int] = Field(default=None)

    part: Optional["Part"] = Relationship(back_populates="suppliers")
    supplier: Optional["Supplier"] = Relationship(back_populates="parts")


class StockLevel(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    part_no: Optional[str] = Field(default=None, foreign_key="part.part_no")
    location_id: Optional[int] = Field(default=None, foreign_key="location.location_id")
    quantity: int = Field(default=0)
    last_updated: Optional[datetime] = Field(default_factory=datetime.now)

    part: Optional["Part"] = Relationship(back_populates="stock_levels")
    location: Optional["Location"] = Relationship(back_populates="stock_levels")


class StockTransaction(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    part_no: Optional[str] = Field(default=None, foreign_key="part.part_no")
    location_id: Optional[int] = Field(default=None, foreign_key="location.location_id")
    transaction_type: TransactionType = Field(default=None)
    quantity: int
    transaction_date: datetime = Field(default_factory=datetime.now)
    work_order_id: Optional[int] = Field(
        default=None, foreign_key="workorder.work_order_id"
    )
    po_no: Optional[str] = Field(default=None, foreign_key="purchaseorder.po_no")
    entered_by: Optional[int] = Field(default=None, foreign_key="user.id")
    notes: Optional[str] = Field(default=None, sa_type=Text)

    part: Optional["Part"] = Relationship(back_populates="transactions")
    location: Optional["Location"] = Relationship(back_populates="stock_transactions")
    work_order: Optional["WorkOrder"] = Relationship(
        back_populates="stock_transactions"
    )
    entered_by_user: Optional["User"] = Relationship(
        back_populates="stock_transactions"
    )


# ------------- Preventative Maintenance ----------------------- #
class PmPlans(SQLModel, table=True):
    pm_id: str = Field(primary_key=True, nullable=False)
    asset_type: AssetCategory = Field(default=None)
    trigger: PmTriggers = Field(default=None)
    frequency: PmFrequency = Field(default=None)
    description: Optional[str] = Field(default=None, sa_type=Text)
    owner: PmOwner = Field(default=None)
    notes: Optional[str] = Field(default=None, sa_type=Text)

    asset_pms: List["AssetPM"] = Relationship(back_populates="pm_plan")


class AssetPM(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, default=None)
    asset_id: Optional[str] = Field(default=None, foreign_key="asset.asset_id")
    pm_plan_id: Optional[str] = Field(default=None, foreign_key="pmplans.pm_id")
    last_service: Optional[date] = Field(default=None)
    next_service: Optional[date] = Field(default=None)
    active: bool = Field(default=True)

    asset: Optional["Asset"] = Relationship(back_populates="asset_pms")
    pm_plan: Optional["PmPlans"] = Relationship(back_populates="asset_pms")
    work_orders: List["WorkOrder"] = Relationship(back_populates="asset_pm")


# ------------- Inspections ----------------------- #
class InspectionTemplate(SQLModel, table=True):
    """Defines the checklist for a particular asset type"""

    id: Optional[int] = Field(primary_key=True, default=None)
    name: str
    asset_type: AssetCategory = Field(default=None)
    frequency: InspectionFrequency = Field(default=InspectionFrequency.daily)
    active: bool = Field(default=True)
    notes: Optional[str] = Field(default=None, sa_type=Text)

    items: List["InspectionTemplateItem"] = Relationship(back_populates="template")
    inspections: List["Inspection"] = Relationship(back_populates="template")


class InspectionTemplateItem(SQLModel, table=True):
    """A single checklist item on a template"""

    id: Optional[int] = Field(primary_key=True, default=None)
    template_id: Optional[int] = Field(
        default=None, foreign_key="inspectiontemplate.id"
    )
    question: str
    category: Optional[str] = Field(default=None)  # e.g. Safety, Mechanical, Electrical
    is_critical: bool = Field(default=False)  # if failed, flags inspection immediately
    order: Optional[int] = Field(default=None)  # display order on the form

    template: Optional["InspectionTemplate"] = Relationship(back_populates="items")
    results: List["InspectionResult"] = Relationship(back_populates="template_item")


class Inspection(SQLModel, table=True):
    """A single completed inspection for an asset"""

    id: Optional[int] = Field(primary_key=True, default=None)
    inspection_no: Optional[str] = Field(default=None, unique=True)  # e.g INS-2026-001, auto-generated
    asset_id: Optional[str] = Field(default=None, foreign_key="asset.asset_id")
    template_id: Optional[int] = Field(
        default=None, foreign_key="inspectiontemplate.id"
    )
    inspected_by: Optional[int] = Field(default=None, foreign_key="user.id")
    inspection_date: date
    inspection_time: Optional[time] = Field(default=None)
    overall_result: InspectionItemResult = Field(default=None)
    submitted: bool = Field(default=False)
    submitted_date: Optional[datetime] = Field(default=None)
    notes: Optional[str] = Field(default=None, sa_type=Text)

    asset: Optional["Asset"] = Relationship(back_populates="inspections")
    template: Optional["InspectionTemplate"] = Relationship(
        back_populates="inspections"
    )
    inspector: Optional["User"] = Relationship(back_populates="inspections")
    results: List["InspectionResult"] = Relationship(back_populates="inspection")


class InspectionResult(SQLModel, table=True):
    """The result for each checklist item on a completed inspection"""

    id: Optional[int] = Field(primary_key=True, default=None)
    inspection_id: Optional[int] = Field(default=None, foreign_key="inspection.id")
    template_item_id: Optional[int] = Field(
        default=None, foreign_key="inspectiontemplateitem.id"
    )
    result: InspectionItemResult = Field(default=None)
    notes: Optional[str] = Field(default=None, sa_type=Text)
    work_order_id: Optional[int] = Field(
        default=None, foreign_key="workorder.work_order_id"
    )  # if fail spawns a WO

    inspection: Optional["Inspection"] = Relationship(back_populates="results")
    template_item: Optional["InspectionTemplateItem"] = Relationship(
        back_populates="results"
    )
    work_order: Optional["WorkOrder"] = Relationship(
        back_populates="inspection_results"
    )


class CommodityRate(SQLModel, table=True):
    """Tracks the bale commodity price over time (USD per lb).
    The rate in effect for a given date is the record with the highest
    effective_date that is <= that date.
    """

    id: Optional[int] = Field(primary_key=True, default=None)
    effective_date: date = Field(index=True)
    rate_per_lb: float = Field(description="USD per pound")
    notes: Optional[str] = Field(default=None, sa_type=Text)
